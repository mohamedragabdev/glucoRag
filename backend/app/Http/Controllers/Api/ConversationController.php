<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\StoreConversationRequest;
use App\Http\Resources\ConversationResource;
use App\Models\Conversation;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class ConversationController extends Controller
{
    public function index(Request $request): AnonymousResourceCollection
    {
        $conversations = $request->user()
            ->conversations()
            ->orderBy('updated_at', 'desc')
            ->get();

        return ConversationResource::collection($conversations);
    }

    public function store(StoreConversationRequest $request): JsonResponse
    {
        $conversation = $request->user()->conversations()->create([
            'title' => $request->validated('title') ?: 'New Conversation',
        ]);

        return (new ConversationResource($conversation))
            ->response()
            ->setStatusCode(201);
    }

    public function show(Conversation $conversation): ConversationResource
    {
        return new ConversationResource($conversation->load(['messages.citations']));
    }

    public function destroy(Conversation $conversation): Response
    {
        $conversation->delete();

        return response()->noContent();
    }
}
