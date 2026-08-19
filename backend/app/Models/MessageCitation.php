<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class MessageCitation extends Model
{
    use HasFactory;

    protected $fillable = [
        'message_id',
        'document_id',
        'chunk_id',
        'source_title',
        'page_number',
        'similarity_score',
    ];

    protected function casts(): array
    {
        return [
            'page_number' => 'integer',
            'similarity_score' => 'float',
        ];
    }

    public function message(): BelongsTo
    {
        return $this->belongsTo(Message::class);
    }
}
