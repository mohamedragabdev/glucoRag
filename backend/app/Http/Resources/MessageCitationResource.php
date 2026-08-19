<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class MessageCitationResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'message_id' => $this->message_id,
            'document_id' => $this->document_id,
            'chunk_id' => $this->chunk_id,
            'source_title' => $this->source_title,
            'page_number' => $this->page_number,
            'created_at' => $this->created_at,
        ];
    }
}
