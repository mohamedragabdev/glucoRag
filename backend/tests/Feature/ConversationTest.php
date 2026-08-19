<?php

namespace Tests\Feature;

use App\Models\Conversation;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ConversationTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_list_their_conversations(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();

        $c1 = Conversation::create(['user_id' => $user1->id, 'title' => 'User 1 Conversation']);
        $c2 = Conversation::create(['user_id' => $user2->id, 'title' => 'User 2 Conversation']);

        $response = $this->actingAs($user1)
            ->getJson('/api/conversations');

        $response->assertStatus(200)
            ->assertJsonCount(1, 'data')
            ->assertJsonFragment(['id' => $c1->id, 'title' => 'User 1 Conversation'])
            ->assertJsonMissing(['id' => $c2->id, 'title' => 'User 2 Conversation']);
    }

    public function test_user_can_create_conversation(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)
            ->postJson('/api/conversations', [
                'title' => 'T2D Screening in Asymptomatic Adults',
            ]);

        $response->assertStatus(201)
            ->assertJsonFragment(['title' => 'T2D Screening in Asymptomatic Adults']);

        $this->assertDatabaseHas('conversations', [
            'user_id' => $user->id,
            'title' => 'T2D Screening in Asymptomatic Adults',
        ]);
    }

    public function test_user_can_view_their_conversation(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'Screening Intervals',
        ]);

        $response = $this->actingAs($user)
            ->getJson("/api/conversations/{$conversation->id}");

        $response->assertStatus(200)
            ->assertJsonFragment(['id' => $conversation->id, 'title' => 'Screening Intervals']);
    }

    public function test_user_cannot_view_another_users_conversation(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();

        $conversation = Conversation::create([
            'user_id' => $user2->id,
            'title' => 'Confidential Conversation',
        ]);

        $response = $this->actingAs($user1)
            ->getJson("/api/conversations/{$conversation->id}");

        $response->assertStatus(403);
    }

    public function test_user_can_delete_their_conversation(): void
    {
        $user = User::factory()->create();
        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'To be deleted',
        ]);

        $response = $this->actingAs($user)
            ->deleteJson("/api/conversations/{$conversation->id}");

        $response->assertStatus(204);
        $this->assertDatabaseMissing('conversations', ['id' => $conversation->id]);
    }

    public function test_user_cannot_delete_another_users_conversation(): void
    {
        $user1 = User::factory()->create();
        $user2 = User::factory()->create();

        $conversation = Conversation::create([
            'user_id' => $user2->id,
            'title' => 'Protected Conversation',
        ]);

        $response = $this->actingAs($user1)
            ->deleteJson("/api/conversations/{$conversation->id}");

        $response->assertStatus(403);
        $this->assertDatabaseHas('conversations', ['id' => $conversation->id]);
    }
}
