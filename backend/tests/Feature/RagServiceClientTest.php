<?php

namespace Tests\Feature;

use App\Exceptions\RagServiceException;
use App\Services\RagServiceClient;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class RagServiceClientTest extends TestCase
{
    public function test_client_sends_authenticated_request(): void
    {
        Http::fake([
            '*/rag/query' => Http::response([
                'request_id' => 'req-001',
                'status' => 'answered',
                'answer' => 'ADA recommends screening at age 35.',
                'confidence' => 'high',
                'safety_status' => 'in_scope',
                'model' => 'openai/gpt-4o-mini',
                'citations' => [],
            ], 200),
        ]);

        $client = new RagServiceClient();
        $response = $client->query('When to screen?', [], 'req-001');

        $this->assertEquals('answered', $response['status']);
        $this->assertEquals('ADA recommends screening at age 35.', $response['answer']);

        Http::assertSent(function ($request) {
            return $request->hasHeader('X-Internal-Secret') &&
                   $request->url() === 'http://localhost:8001/rag/query' &&
                   $request['question'] === 'When to screen?';
        });
    }

    public function test_client_throws_exception_on_server_error(): void
    {
        Http::fake([
            '*/rag/query' => Http::response(['error' => 'Internal server error'], 500),
        ]);

        $client = new RagServiceClient();

        try {
            $client->query('When to screen?');
            $this->fail('Expected an upstream RAG service error.');
        } catch (RagServiceException $exception) {
            $this->assertSame('RAG Service request failed with HTTP 500', $exception->getMessage());
            $this->assertStringNotContainsString('Internal server error', $exception->getMessage());
        }
    }
}
