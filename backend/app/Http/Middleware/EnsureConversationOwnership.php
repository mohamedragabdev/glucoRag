<?php

namespace App\Http\Middleware;

use App\Models\Conversation;
use App\Models\Message;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class EnsureConversationOwnership
{
    public function handle(Request $request, Closure $next): Response
    {
        $user = $request->user();

        if (! $user) {
            return response()->json(['message' => 'Unauthenticated.'], 401);
        }

        $conversationId = $request->route('conversation') ?? $request->route('id');

        if ($conversationId) {
            $conversation = $conversationId instanceof Conversation
                ? $conversationId
                : Conversation::find($conversationId);

            if (! $conversation) {
                return response()->json(['message' => 'Conversation not found.'], 404);
            }

            if ($conversation->user_id !== $user->id) {
                return response()->json(['message' => 'Forbidden. You do not own this conversation.'], 403);
            }
        }

        $messageId = $request->route('message');
        if ($messageId) {
            $message = $messageId instanceof Message
                ? $messageId
                : Message::with('conversation')->find($messageId);

            if (! $message) {
                return response()->json(['message' => 'Message not found.'], 404);
            }

            if ($message->conversation->user_id !== $user->id) {
                return response()->json(['message' => 'Forbidden. You do not own this message.'], 403);
            }
        }

        return $next($request);
    }
}
