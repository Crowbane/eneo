<script lang="ts">
  import { m } from "$lib/paraglide/messages";

  let { data } = $props();

  type Message = {
    role: "user" | "assistant";
    content: string;
  };

  let messages = $state<Message[]>([]);
  let input = $state("");
  let isStreaming = $state(false);
  let messagesContainer: HTMLDivElement | undefined = $state();

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  async function sendMessage() {
    const question = input.trim();
    if (!question || isStreaming) return;

    input = "";
    messages.push({ role: "user", content: question });
    messages.push({ role: "assistant", content: "" });
    isStreaming = true;

    // Trigger scroll after DOM update
    await tick();
    scrollToBottom();

    try {
      const res = await fetch(
        `${data.baseUrl}/api/v1/public/assistants/${data.token}/ask/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream"
          },
          body: JSON.stringify({ question, stream: true })
        }
      );

      if (!res.ok) {
        messages[messages.length - 1].content = "Sorry, something went wrong.";
        isStreaming = false;
        return;
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        messages[messages.length - 1].content = "Sorry, something went wrong.";
        isStreaming = false;
        return;
      }

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data:")) {
            const text = line.slice(5).trim();
            if (text) {
              messages[messages.length - 1].content += text;
              scrollToBottom();
            }
          }
        }
      }
    } catch {
      if (!messages[messages.length - 1].content) {
        messages[messages.length - 1].content = "Sorry, something went wrong.";
      }
    }

    isStreaming = false;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  import { tick } from "svelte";
</script>

<svelte:head>
  <title>{data.assistant.name}</title>
</svelte:head>

<div class="flex h-full flex-col">
  <!-- Header -->
  <header class="border-default flex items-center gap-3 border-b px-6 py-4">
    {#if data.assistant.icon_id}
      <img
        src="{data.baseUrl}/api/v1/icons/{data.assistant.icon_id}/"
        alt=""
        class="h-10 w-10 rounded-lg object-cover"
      />
    {/if}
    <div>
      <h1 class="text-primary text-lg font-semibold">{data.assistant.name}</h1>
      {#if data.assistant.description}
        <p class="text-muted text-sm">{data.assistant.description}</p>
      {/if}
    </div>
  </header>

  <!-- Messages -->
  <div class="flex-1 overflow-y-auto px-4 py-6" bind:this={messagesContainer}>
    <div class="mx-auto max-w-2xl space-y-4">
      {#if messages.length === 0}
        <div class="text-muted flex flex-col items-center justify-center py-20 text-center">
          <p class="text-lg font-medium">{data.assistant.name}</p>
          {#if data.assistant.description}
            <p class="mt-1 text-sm">{data.assistant.description}</p>
          {/if}
        </div>
      {/if}

      {#each messages as message}
        <div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
          <div
            class="max-w-[80%] rounded-2xl px-4 py-2 {message.role === 'user'
              ? 'bg-primary text-on-fill'
              : 'bg-hover-overlay text-primary'}"
          >
            <p class="whitespace-pre-wrap text-sm">{message.content}{#if isStreaming && message === messages[messages.length - 1] && message.role === 'assistant'}<span class="animate-pulse">▊</span>{/if}</p>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Input -->
  <div class="border-default border-t px-4 py-3">
    <div class="mx-auto flex max-w-2xl gap-2">
      <textarea
        class="bg-secondary border-default text-primary placeholder:text-muted min-h-[44px] flex-1 resize-none rounded-xl border px-4 py-2.5 text-sm focus:outline-none"
        placeholder={m.public_chat_placeholder()}
        rows={1}
        bind:value={input}
        onkeydown={handleKeydown}
        disabled={isStreaming}
      ></textarea>
      <button
        aria-label="Send message"
        class="bg-primary text-on-fill flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-opacity disabled:opacity-40"
        onclick={sendMessage}
        disabled={!input.trim() || isStreaming}
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="h-5 w-5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
        </svg>
      </button>
    </div>
  </div>

  <!-- Footer -->
  <footer class="text-muted px-4 pb-3 text-center text-xs">
    {m.powered_by_eneo()}
  </footer>
</div>
