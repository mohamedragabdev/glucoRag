<?php

namespace Tests\Feature;

use App\Jobs\ProcessRagMessageJob;
use App\Models\Conversation;
use App\Models\Message;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

class MessageTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_list_messages_in_conversation(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'Screening test message list',
        ]);

        $msg1 = $conversation->messages()->create([
            'role' => 'user',
            'content' => 'What is the fasting plasma glucose threshold for diabetes screening?',
            'status' => 'completed',
        ]);

        $msg2 = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => 'FPG ≥ 126 mg/dL (7.0 mmol/L) warrants confirmation.',
            'status' => 'completed',
        ]);

        $response = $this->actingAs($user)
            ->getJson("/api/conversations/{$conversation->id}/messages");

        $response->assertStatus(200)
            ->assertJsonCount(2, 'data')
            ->assertJsonFragment(['id' => $msg1->id, 'role' => 'user'])
            ->assertJsonFragment(['id' => $msg2->id, 'role' => 'assistant']);
    }

    public function test_user_can_send_message_and_receives_202_accepted(): void
    {
        Queue::fake();

        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'New Conversation',
        ]);

        $response = $this->actingAs($user)
            ->postJson("/api/conversations/{$conversation->id}/messages", [
                'content' => 'When should screening begin for overweight individuals with risk factors?',
            ]);

        $response->assertStatus(202)
            ->assertJsonStructure([
                'data' => [
                    'user_message' => ['id', 'conversation_id', 'role', 'content', 'status'],
                    'assistant_message' => ['id', 'conversation_id', 'role', 'content', 'status'],
                ],
            ]);

        $responseData = $response->json('data');
        $this->assertEquals('completed', $responseData['user_message']['status']);
        $this->assertEquals('pending', $responseData['assistant_message']['status']);
        $this->assertNull($responseData['assistant_message']['content']);

        Queue::assertPushed(ProcessRagMessageJob::class, function ($job) use ($responseData) {
            return $job->messageId === $responseData['assistant_message']['id'];
        });
    }

    public function test_message_content_validation_rules(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'Validation Conversation',
        ]);

        // Empty message
        $responseEmpty = $this->actingAs($user)
            ->postJson("/api/conversations/{$conversation->id}/messages", [
                'content' => '',
            ]);
        $responseEmpty->assertStatus(422)
            ->assertJsonValidationErrors(['content']);

        // Oversized message (> 2000 chars)
        $oversized = str_repeat('a', 2001);
        $responseOversized = $this->actingAs($user)
            ->postJson("/api/conversations/{$conversation->id}/messages", [
                'content' => $oversized,
            ]);
        $responseOversized->assertStatus(422)
            ->assertJsonValidationErrors(['content']);
    }

    public function test_user_cannot_send_message_to_another_users_conversation(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();

        $conversation = Conversation::create([
            'user_id' => $user2->id,
            'title' => 'Other User Conversation',
        ]);

        $response = $this->actingAs($user1)
            ->postJson("/api/conversations/{$conversation->id}/messages", [
                'content' => 'Unauthorized attempt',
            ]);

        $response->assertStatus(403);
    }

    public function test_user_can_get_single_message(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'Message Polling',
        ]);

        $assistantMessage = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => 'Processing complete.',
            'status' => 'completed',
        ]);

        $response = $this->actingAs($user)
            ->getJson("/api/messages/{$assistantMessage->id}");

        $response->assertStatus(200)
            ->assertJsonFragment([
                'id' => $assistantMessage->id,
                'status' => 'completed',
                'content' => 'Processing complete.',
            ]);
    }

    public function test_user_cannot_get_message_belonging_to_another_user(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();

        $conversation = Conversation::create([
            'user_id' => $user2->id,
            'title' => 'Other User Conversation',
        ]);

        $message = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => 'Private content',
            'status' => 'completed',
        ]);

        $response = $this->actingAs($user1)
            ->getJson("/api/messages/{$message->id}");

        $response->assertStatus(403);
    }
}
