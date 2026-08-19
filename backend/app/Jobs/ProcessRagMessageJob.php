<?php

namespace App\Jobs;

use App\Exceptions\RagServiceException;
use App\Models\Message;
use App\Models\MessageCitation;
use App\Services\RagServiceClient;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Throwable;

class ProcessRagMessageJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    public array $backoff = [10, 30, 90];

    public int $messageId;

    public function __construct(int $messageId)
    {
        $this->messageId = $messageId;
    }

    public function handle(RagServiceClient $ragClient): void
    {
        $assistantMessage = Message::with('conversation.messages')->find($this->messageId);

        if (! $assistantMessage) {
            Log::warning("ProcessRagMessageJob: Assistant message {$this->messageId} not found.");
            return;
        }

        $conversation = $assistantMessage->conversation;

        // Get the latest user message preceding this assistant message
        $userMessage = $conversation->messages()
            ->where('role', 'user')
            ->where('id', '<', $assistantMessage->id)
            ->orderBy('id', 'desc')
            ->first();

        if (! $userMessage) {
            Log::warning("ProcessRagMessageJob: No user message found for assistant message {$this->messageId}.");
            $assistantMessage->update([
                'status' => 'failed',
                'error_message' => 'No question prompt was found to process.',
            ]);
            return;
        }

        // Get the last N conversation turns for context
        $history = $conversation->messages()
            ->where('id', '<', $userMessage->id)
            ->where('status', 'completed')
            ->whereNotNull('content')
            ->orderBy('id', 'desc')
            ->take(6)
            ->get()
            ->reverse()
            ->map(function ($msg) {
                return [
                    'role' => $msg->role,
                    'content' => $msg->content,
                ];
            })
            ->values()
            ->toArray();

        $requestId = (string) Str::uuid();

        try {
            $response = $ragClient->query($userMessage->content, $history, $requestId);

            $status = $response['status'] ?? 'completed';
            $answer = $response['answer'] ?? null;
            $citations = $response['citations'] ?? [];

            // If status is out_of_scope or insufficient_evidence, set appropriate content
            $isArabic = preg_match('/[\x{0600}-\x{06FF}]/u', $userMessage->content);
            if ($status === 'out_of_scope') {
                $defaultRefusal = $isArabic
                    ? "عذرًا، GlucoRAG متخصص فقط في إرشادات فحص السكري من النوع الثاني. يمكنني مساعدتك في معايير الفحص، الفحوصات المستخدمة، الفئات المستهدفة، الحدود المرجعية، وفترات إعادة الفحص."
                    : "I’m sorry, but GlucoRAG is limited to Type 2 Diabetes screening guidance. I can help with screening criteria, recommended screening tests, eligibility, thresholds, and screening intervals.";
                $answer = $answer ?? $defaultRefusal;
            } elseif ($status === 'insufficient_evidence') {
                $defaultInsufficient = $isArabic
                    ? "لم أجد معلومات كافية في المستندات المرجعية الحالية للإجابة عن هذا السؤال بشكل موثوق."
                    : "I couldn't find sufficient information in the current reference documents to answer this reliably.";
                $answer = $answer ?? $defaultInsufficient;
            } elseif ($status === 'error') {
                $assistantMessage->update([
                    'status' => 'failed',
                    'error_message' => 'An error occurred while processing your request.',
                ]);
                return;
            }

            DB::transaction(function () use ($assistantMessage, $citations, $status, $answer) {
                $assistantMessage->update([
                    'content' => $answer,
                    'status' => 'completed',
                    'error_message' => null,
                ]);

                if (! empty($citations) && $status === 'answered') {
                    foreach ($citations as $citation) {
                        MessageCitation::updateOrCreate(
                            [
                                'message_id' => $assistantMessage->id,
                                'chunk_id' => $citation['chunk_id'] ?? 'unknown_chunk',
                            ],
                            [
                                'document_id' => $citation['document_id'] ?? 'unknown_doc',
                                'source_title' => $citation['title'] ?? 'Reference Document',
                                'page_number' => $citation['page_number'] ?? null,
                                'similarity_score' => $citation['similarity_score'] ?? null,
                            ],
                        );
                    }
                }
            });

            $conversation->touch();

        } catch (RagServiceException $e) {
            Log::error("ProcessRagMessageJob RAG Service error: " . $e->getMessage(), [
                'message_id' => $this->messageId,
                'request_id' => $requestId,
            ]);

            // If 4xx, it's non-retryable
            if ($e->getCode() >= 400 && $e->getCode() < 500) {
                $this->fail($e);
                return;
            }

            throw $e; // Triggers queue retry for transient 5xx/network errors
        }
    }

    public function failed(?Throwable $exception): void
    {
        Log::error("ProcessRagMessageJob failed permanently for message {$this->messageId}: " . ($exception ? $exception->getMessage() : 'Unknown error'));

        $assistantMessage = Message::find($this->messageId);
        if ($assistantMessage) {
            $assistantMessage->update([
                'status' => 'failed',
                'error_message' => "We couldn't process your question right now. Please try again.",
            ]);
        }
    }
}
