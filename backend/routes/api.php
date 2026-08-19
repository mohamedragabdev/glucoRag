<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\ConversationController;
use App\Http\Controllers\Api\MessageController;
use App\Http\Middleware\EnsureConversationOwnership;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

// Public Health Check Endpoint
Route::get('/health', function () {
    return response()->json([
        'status' => 'ok',
        'service' => 'GlucoRAG Backend API',
        'timestamp' => now()->toIso8601String(),
    ]);
});

// Auth Routes (Public, throttled)
Route::middleware('throttle:api')->group(function () {
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login', [AuthController::class, 'login']);
});

// Authenticated Routes
Route::middleware(['auth:sanctum', 'throttle:api'])->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/user', function (Request $request) {
        return response()->json(['user' => $request->user()]);
    });

    // Conversations
    Route::get('/conversations', [ConversationController::class, 'index']);
    Route::post('/conversations', [ConversationController::class, 'store']);

    // Conversation & Message ownership-protected routes
    Route::middleware(EnsureConversationOwnership::class)->group(function () {
        Route::get('/conversations/{conversation}', [ConversationController::class, 'show']);
        Route::delete('/conversations/{conversation}', [ConversationController::class, 'destroy']);

        Route::get('/conversations/{conversation}/messages', [MessageController::class, 'index']);
        Route::post('/conversations/{conversation}/messages', [MessageController::class, 'store'])
            ->middleware('throttle:messages');
        Route::get('/messages/{message}', [MessageController::class, 'show']);
    });
});
