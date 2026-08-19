<?php

namespace Tests\Feature;

use App\Exceptions\RagServiceException;
use App\Jobs\ProcessRagMessageJob;
use App\Models\Conversation;
use App\Models\Message;
use App\Models\User;
use App\Services\RagServiceClient;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Tests\TestCase;

class QueueJobTest extends TestCase
{
    use RefreshDatabase;

    public function test_job_processes_successful_rag_response_with_citations(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'ADA Screening Guidelines',
        ]);

        $userMsg = $conversation->messages()->create([
            'role' => 'user',
            'content' => 'What is the screening criteria for prediabetes?',
            'status' => 'completed',
        ]);

        $assistantMsg = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => null,
            'status' => 'pending',
        ]);

        $mockRagClient = Mockery::mock(RagServiceClient::class);
        $mockRagClient->shouldReceive('query')
            ->once()
            ->with($userMsg->content, Mockery::type('array'), Mockery::type('string'))
            ->andReturn([
                'request_id' => 'req-12345',
                'status' => 'answered',
                'answer' => 'Prediabetes screening criteria includes FPG 100-125 mg/dL or 2-h PG 140-199 mg/dL or A1C 5.7-6.4%.',
                'confidence' => 'high',
                'safety_status' => 'in_scope',
                'model' => 'openai/gpt-4o-mini',
                'citations' => [
                    [
                        'chunk_id' => 'ada_2024_p5_c1',
                        'document_id' => 'ada_2024',
                        'title' => 'ADA Standards of Medical Care in Diabetes 2024',
                        'page_number' => 5,
                        'similarity_score' => 0.9450,
                    ],
                ],
            ]);

        $job = new ProcessRagMessageJob($assistantMsg->id);
        $job->handle($mockRagClient);

        $assistantMsg->refresh();
        $this->assertEquals('completed', $assistantMsg->status);
        $this->assertStringContainsString('Prediabetes screening criteria', $assistantMsg->content);
        $this->assertNull($assistantMsg->error_message);

        $this->assertCount(1, $assistantMsg->citations);
        $citation = $assistantMsg->citations->first();
        $this->assertEquals('ada_2024_p5_c1', $citation->chunk_id);
        $this->assertEquals('ADA Standards of Medical Care in Diabetes 2024', $citation->source_title);
        $this->assertEquals(5, $citation->page_number);
    }

    public function test_job_handles_insufficient_evidence(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create(['user_id' => $user->id, 'title' => 'Insufficient Test']);

        $userMsg = $conversation->messages()->create([
            'role' => 'user',
            'content' => 'Rare exotic biomarker for screening?',
            'status' => 'completed',
        ]);

        $assistantMsg = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => null,
            'status' => 'pending',
        ]);

        $mockRagClient = Mockery::mock(RagServiceClient::class);
        $mockRagClient->shouldReceive('query')
            ->once()
            ->andReturn([
                'request_id' => 'req-67890',
                'status' => 'insufficient_evidence',
                'answer' => null,
                'confidence' => null,
                'safety_status' => 'in_scope',
                'model' => 'openai/gpt-4o-mini',
                'citations' => [],
            ]);

        $job = new ProcessRagMessageJob($assistantMsg->id);
        $job->handle($mockRagClient);

        $assistantMsg->refresh();
        $this->assertEquals('completed', $assistantMsg->status);
        $this->assertStringContainsString("I couldn't find sufficient information in the current reference documents", $assistantMsg->content);
        $this->assertCount(0, $assistantMsg->citations);
    }

    public function test_job_handles_out_of_scope(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create(['user_id' => $user->id, 'title' => 'Out of Scope']);

        $userMsg = $conversation->messages()->create([
            'role' => 'user',
            'content' => 'What is the surgical treatment for appendicitis?',
            'status' => 'completed',
        ]);

        $assistantMsg = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => null,
            'status' => 'pending',
        ]);

        $mockRagClient = Mockery::mock(RagServiceClient::class);
        $mockRagClient->shouldReceive('query')
            ->once()
            ->andReturn([
                'request_id' => 'req-oos-1',
                'status' => 'out_of_scope',
                'answer' => null,
                'confidence' => null,
                'safety_status' => 'out_of_scope',
                'model' => 'openai/gpt-4o-mini',
                'citations' => [],
            ]);

        $job = new ProcessRagMessageJob($assistantMsg->id);
        $job->handle($mockRagClient);

        $assistantMsg->refresh();
        $this->assertEquals('completed', $assistantMsg->status);
        $this->assertStringContainsString("GlucoRAG is limited to Type 2 Diabetes screening guidance", $assistantMsg->content);
    }

    public function test_job_handles_terminal_failure(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create(['user_id' => $user->id, 'title' => 'Failure test']);

        $conversation->messages()->create([
            'role' => 'user',
            'content' => 'Question',
            'status' => 'completed',
        ]);

        $assistantMsg = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => null,
            'status' => 'pending',
        ]);

        $job = new ProcessRagMessageJob($assistantMsg->id);
        $job->failed(new \Exception('Connection timed out'));

        $assistantMsg->refresh();
        $this->assertEquals('failed', $assistantMsg->status);
        $this->assertStringContainsString("We couldn't process your question right now", $assistantMsg->error_message);
    }
}
