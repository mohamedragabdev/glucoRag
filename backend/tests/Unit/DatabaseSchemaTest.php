<?php

namespace Tests\Unit;

use App\Models\Conversation;
use App\Models\Message;
use App\Models\MessageCitation;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class DatabaseSchemaTest extends TestCase
{
    use RefreshDatabase;

    public function test_models_and_relationships_work_correctly(): void
    {
        $user = User::create([
            'name' => 'Dr. Jane Smith',
            'email' => 'jane@clinic.org',
            'password' => bcrypt('password123'),
        ]);

        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'ADA Screening Guidelines',
        ]);

        $message = Message::create([
            'conversation_id' => $conversation->id,
            'role' => 'assistant',
            'content' => 'Screening for diabetes should begin at age 35 for all adults.',
            'status' => 'completed',
        ]);

        $citation = MessageCitation::create([
            'message_id' => $message->id,
            'document_id' => 'ada_standards_2024',
            'chunk_id' => 'ada_standards_2024_p12_c1',
            'source_title' => 'ADA Standards of Care 2024',
            'page_number' => 12,
            'similarity_score' => 0.8950,
        ]);

        $this->assertEquals(1, $user->conversations()->count());
        $this->assertEquals($user->id, $conversation->user->id);
        $this->assertEquals(1, $conversation->messages()->count());
        $this->assertEquals($conversation->id, $message->conversation->id);
        $this->assertEquals(1, $message->citations()->count());
        $this->assertEquals($message->id, $citation->message->id);
    }

    public function test_cascading_deletes(): void
    {
        $user = User::create([
            'name' => 'Dr. John Doe',
            'email' => 'john@clinic.org',
            'password' => bcrypt('password123'),
        ]);

        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'USPSTF Recommendations',
        ]);

        $message = Message::create([
            'conversation_id' => $conversation->id,
            'role' => 'user',
            'content' => 'What is the screening interval?',
            'status' => 'completed',
        ]);

        $citation = MessageCitation::create([
            'message_id' => $message->id,
            'document_id' => 'uspstf_t2d_2021',
            'chunk_id' => 'uspstf_t2d_2021_p3_c2',
            'source_title' => 'USPSTF Diabetes Screening',
            'page_number' => 3,
            'similarity_score' => 0.9123,
        ]);

        $this->assertDatabaseHas('users', ['id' => $user->id]);
        $this->assertDatabaseHas('conversations', ['id' => $conversation->id]);
        $this->assertDatabaseHas('messages', ['id' => $message->id]);
        $this->assertDatabaseHas('message_citations', ['id' => $citation->id]);

        $user->delete();

        $this->assertDatabaseMissing('users', ['id' => $user->id]);
        $this->assertDatabaseMissing('conversations', ['id' => $conversation->id]);
        $this->assertDatabaseMissing('messages', ['id' => $message->id]);
        $this->assertDatabaseMissing('message_citations', ['id' => $citation->id]);
    }
}
