<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\StoreMessageRequest;
use App\Http\Resources\MessageResource;
use App\Jobs\ProcessRagMessageJob;
use App\Models\Conversation;
use App\Models\Message;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Str;

class MessageController extends Controller
{
    public function index(Conversation $conversation): AnonymousResourceCollection
    {
        $messages = $conversation->messages()
            ->with('citations')
            ->orderBy('id', 'asc')
            ->get();

        return MessageResource::collection($messages);
    }

    public function store(StoreMessageRequest $request, Conversation $conversation): JsonResponse
    {
        $content = $request->validated('content');

        // Auto-title conversation from first message if title is default
        if ($conversation->title === 'New Conversation' || empty($conversation->title)) {
            $conversation->update([
                'title' => Str::limit($content, 40),
            ]);
        }

        $userMessage = $conversation->messages()->create([
            'role' => 'user',
            'content' => $content,
            'status' => 'completed',
        ]);

        $assistantMessage = $conversation->messages()->create([
            'role' => 'assistant',
            'content' => null,
            'status' => 'pending',
        ]);

        $conversation->touch();

        // Dispatch async RAG processing job
        ProcessRagMessageJob::dispatch($assistantMessage->id);

        return response()->json([
            'data' => [
                'user_message' => new MessageResource($userMessage),
                'assistant_message' => new MessageResource($assistantMessage),
            ],
        ], 202);
    }

    public function show(Message $message): MessageResource
    {
        return new MessageResource($message->load('citations'));
    }
}
