<?php

namespace App\Services;

use App\Exceptions\RagServiceException;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class RagServiceClient
{
    protected string $baseUrl;
    protected string $internalSecret;
    protected int $timeout;

    public function __construct()
    {
        $this->baseUrl = rtrim(Config::get('rag.url', 'http://localhost:8001'), '/');
        $this->internalSecret = Config::get('rag.internal_secret', '');
        $this->timeout = (int) Config::get('rag.timeout', 30);
    }

    /**
     * Query the RAG service.
     *
     * @param string $question
     * @param array $conversationHistory
     * @param string $requestId
     * @return array
     * @throws RagServiceException
     */
    public function query(string $question, array $conversationHistory = [], string $requestId = ''): array
    {
        $url = "{$this->baseUrl}/rag/query";

        try {
            $response = Http::withHeaders([
                'X-Internal-Secret' => $this->internalSecret,
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
            ])
            ->timeout($this->timeout)
            ->post($url, [
                'question' => $question,
                'conversation_history' => $conversationHistory,
                'request_id' => $requestId,
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            $statusCode = $response->status();
            Log::error("RAG Service returned an unsuccessful response", [
                'request_id' => $requestId,
                'status_code' => $statusCode,
            ]);

            throw new RagServiceException("RAG Service request failed with HTTP {$statusCode}", $statusCode);

        } catch (\Illuminate\Http\Client\ConnectionException $e) {
            Log::error("RAG Service connection error: {$e->getMessage()}", [
                'request_id' => $requestId,
            ]);
            throw new RagServiceException("Unable to connect to RAG Service: {$e->getMessage()}", 503, $e);
        } catch (\Throwable $e) {
            if ($e instanceof RagServiceException) {
                throw $e;
            }
            Log::error("RAG Service client exception: {$e->getMessage()}", [
                'request_id' => $requestId,
            ]);
            throw new RagServiceException("RAG Service error: {$e->getMessage()}", 500, $e);
        }
    }
}
