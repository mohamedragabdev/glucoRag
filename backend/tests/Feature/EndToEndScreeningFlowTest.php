<?php

namespace Tests\Feature;

use App\Models\Conversation;
use App\Models\User;
use App\Services\RagServiceClient;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Mockery;
use Tests\TestCase;

class EndToEndScreeningFlowTest extends TestCase
{
    use RefreshDatabase;

    public function test_end_to_end_uspstf_screening_request_flow(): void
    {
        $user = User::factory()->create();
        Sanctum::actingAs($user);

        // Bind mock RAG client before dispatch
        $mockRagClient = Mockery::mock(RagServiceClient::class);
        $mockRagClient->shouldReceive('query')
            ->once()
            ->with(
                'What is the recommended screening age according to the USPSTF?',
                Mockery::type('array'),
                Mockery::type('string')
            )
            ->andReturn([
                'request_id' => 'req-uspstf-e2e-1',
                'status' => 'answered',
                'answer' => 'According to the USPSTF 2021 recommendations, screening for prediabetes and type 2 diabetes is recommended in adults aged 35 to 70 years who are overweight or obese.',
                'confidence' => 'high',
                'safety_status' => 'in_scope',
                'model' => 'openrouter/free',
                'citations' => [
                    [
                        'document_id' => 'uspstf_2021',
                        'chunk_id' => 'uspstf_2021_p2_c1',
                        'title' => 'USPSTF Screening for Prediabetes and Type 2 Diabetes in Adults',
                        'page_number' => 2,
                        'similarity_score' => 0.925,
                    ],
                ],
            ]);
        $this->app->instance(RagServiceClient::class, $mockRagClient);

        // 1. Create conversation
        $convResponse = $this->postJson('/api/conversations', [
            'title' => 'USPSTF Screening Query',
        ]);
        $convResponse->assertStatus(201);
        $conversationId = $convResponse->json('data.id');

        // 2. Post user message through standard HTTP API (triggers synchronous queue job in test)
        $msgResponse = $this->postJson("/api/conversations/{$conversationId}/messages", [
            'content' => 'What is the recommended screening age according to the USPSTF?',
        ]);

        $msgResponse->assertStatus(202);

        // 3. Fetch the conversation messages from the HTTP API (as the frontend does)
        $fetchResponse = $this->getJson("/api/conversations/{$conversationId}/messages");
        $fetchResponse->assertStatus(200);

        $messages = $fetchResponse->json('data');
        $this->assertCount(2, $messages);

        $assistantMsg = $messages[1];
        $this->assertEquals('assistant', $assistantMsg['role']);
        $this->assertEquals('completed', $assistantMsg['status']);
        $this->assertNull($assistantMsg['error_message']);
        $this->assertStringContainsString('USPSTF 2021 recommendations', $assistantMsg['content']);
        $this->assertCount(1, $assistantMsg['citations']);
        $this->assertEquals('uspstf_2021_p2_c1', $assistantMsg['citations'][0]['chunk_id']);
        $this->assertEquals('USPSTF Screening for Prediabetes and Type 2 Diabetes in Adults', $assistantMsg['citations'][0]['source_title']);
    }

    public function test_end_to_end_arabic_screening_flow(): void
    {
        $user = User::factory()->create();
        Sanctum::actingAs($user);

        $mockRagClient = Mockery::mock(RagServiceClient::class);
        $mockRagClient->shouldReceive('query')
            ->once()
            ->andReturn([
                'request_id' => 'req-ar-e2e-2',
                'status' => 'answered',
                'answer' => 'توصي فرقة الخدمات الوقائية الأمريكية (USPSTF) بإجراء فحص السكري من النوع الثاني ومقدمات السكري للبالغين الذين تتراوح أعمارهم بين 35 و70 عاماً والذين يعانون من زيادة الوزن أو السمنة.',
                'confidence' => 'high',
                'safety_status' => 'in_scope',
                'model' => 'openrouter/free',
                'citations' => [
                    [
                        'document_id' => 'uspstf_2021',
                        'chunk_id' => 'uspstf_2021_p2_c1',
                        'title' => 'USPSTF Screening Recommendations',
                        'page_number' => 2,
                        'similarity_score' => 0.94,
                    ],
                ],
            ]);
        $this->app->instance(RagServiceClient::class, $mockRagClient);

        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'استفسار فحص السكري',
        ]);

        $msgResponse = $this->postJson("/api/conversations/{$conversation->id}/messages", [
            'content' => 'ما هي توصيات USPSTF لفحص السكري من النوع الثاني؟',
        ]);

        $msgResponse->assertStatus(202);

        $fetchResponse = $this->getJson("/api/conversations/{$conversation->id}/messages");
        $fetchResponse->assertStatus(200);

        $messages = $fetchResponse->json('data');
        $assistantMsg = $messages[1];
        $this->assertEquals('completed', $assistantMsg['status']);
        $this->assertStringContainsString('USPSTF', $assistantMsg['content']);
        $this->assertCount(1, $assistantMsg['citations']);
    }

    public function test_end_to_end_out_of_scope_treatment_refusal(): void
    {
        $user = User::factory()->create();
        Sanctum::actingAs($user);

        $mockRagClient = Mockery::mock(RagServiceClient::class);
        $mockRagClient->shouldReceive('query')
            ->once()
            ->andReturn([
                'request_id' => 'req-oos-e2e-3',
                'status' => 'out_of_scope',
                'answer' => "I’m sorry, but GlucoRAG is limited to Type 2 Diabetes screening guidance. I can help with screening criteria, recommended screening tests, eligibility, thresholds, and screening intervals.",
                'confidence' => null,
                'safety_status' => 'refused_treatment',
                'model' => 'openrouter/free',
                'citations' => [],
            ]);
        $this->app->instance(RagServiceClient::class, $mockRagClient);

        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'Treatment Query',
        ]);

        $msgResponse = $this->postJson("/api/conversations/{$conversation->id}/messages", [
            'content' => 'How do I treat diabetes?',
        ]);

        $msgResponse->assertStatus(202);

        $fetchResponse = $this->getJson("/api/conversations/{$conversation->id}/messages");
        $fetchResponse->assertStatus(200);

        $messages = $fetchResponse->json('data');
        $assistantMsg = $messages[1];
        $this->assertEquals('completed', $assistantMsg['status']);
        $this->assertStringContainsString('GlucoRAG is limited to Type 2 Diabetes screening guidance', $assistantMsg['content']);
        $this->assertCount(0, $assistantMsg['citations']);
    }
}
