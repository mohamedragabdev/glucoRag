<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('message_citations', function (Blueprint $table) {
            $table->unique(['message_id', 'chunk_id'], 'message_citations_message_chunk_unique');
        });
    }

    public function down(): void
    {
        Schema::table('message_citations', function (Blueprint $table) {
            $table->dropUnique('message_citations_message_chunk_unique');
        });
    }
};
