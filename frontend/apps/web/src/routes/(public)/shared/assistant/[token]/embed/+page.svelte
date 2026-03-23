<script lang="ts">
  import { tick } from "svelte";
  import { fly } from "svelte/transition";
  import { Markdown } from "@intric/ui";
  import EneoWordMark from "$lib/assets/EneoWordMark.svelte";
  import { IconEnter } from "@intric/icons/enter";
  import { IconStopCircle } from "@intric/icons/stop-circle";
  import { m } from "$lib/paraglide/messages";

  let { data } = $props();

  type Message = {
    role: "user" | "assistant";
    content: string;
    id: number;
  };

  let messageId = 0;
  let messages = $state<Message[]>([]);
  let input = $state("");
  let isStreaming = $state(false);
  let scrollContainer: HTMLDivElement | undefined = $state();
  let abortController: AbortController | undefined;
  let textareaEl: HTMLTextAreaElement | undefined = $state();

  function scrollToBottom() {
    if (scrollContainer) {
      setTimeout(() => {
        scrollContainer!.scrollTo({ top: scrollContainer!.scrollHeight, behavior: "smooth" });
      }, 10);
    }
  }

  function autoResize() {
    if (!textareaEl) return;
    textareaEl.style.height = "auto";
    textareaEl.style.height = Math.min(textareaEl.scrollHeight, 120) + "px";
  }

  async function sendMessage() {
    const question = input.trim();
    if (!question || isStreaming) return;

    input = "";
    if (textareaEl) {
      textareaEl.style.height = "auto";
    }
    messages.push({ role: "user", content: question, id: messageId++ });
    messages.push({ role: "assistant", content: "", id: messageId++ });
    isStreaming = true;

    await tick();
    scrollToBottom();

    abortController = new AbortController();

    // Build conversation history from completed message pairs
    const history: { question: string; answer: string }[] = [];
    for (let i = 0; i < messages.length - 2; i += 2) {
      if (messages[i].role === "user" && messages[i + 1]?.role === "assistant" && messages[i + 1].content) {
        history.push({
          question: messages[i].content,
          answer: messages[i + 1].content
        });
      }
    }

    try {
      const res = await fetch(
        `${data.baseUrl}/api/v1/public/assistants/${data.token}/ask/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream"
          },
          body: JSON.stringify({ question, stream: true, messages: history }),
          signal: abortController.signal
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
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") {
        // User cancelled
      } else if (!messages[messages.length - 1].content) {
        messages[messages.length - 1].content = "Sorry, something went wrong.";
      }
    }

    isStreaming = false;
    abortController = undefined;

    await tick();
    textareaEl?.focus();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const isAskingDisabled = $derived(input.trim() === "");
</script>

<svelte:head>
  <title>{data.assistant.name}</title>
</svelte:head>

<div class="embed-container flex h-full flex-col">
  <!-- Header -->
  <header class="border-default flex items-center gap-2.5 border-b px-3 py-2.5">
    {#if data.assistant.icon_id}
      <img
        src="{data.baseUrl}/api/v1/icons/{data.assistant.icon_id}/"
        alt=""
        class="h-8 w-8 shrink-0 rounded-lg object-cover"
      />
    {/if}
    <h1 class="text-primary min-w-0 flex-1 truncate text-sm font-semibold">{data.assistant.name}</h1>
    <a href="/" target="_blank" rel="noopener" class="shrink-0 opacity-50 transition-opacity hover:opacity-100" aria-label="Eneo">
      <EneoWordMark class="text-brand-intric h-4 w-14" />
    </a>
  </header>

  <!-- Messages -->
  <div
    class="flex min-h-0 flex-1 flex-col overflow-y-auto"
    bind:this={scrollContainer}
  >
    {#if messages.length > 0}
      <div class="flex flex-grow flex-col gap-1.5 p-3 md:p-5" aria-live="polite">
        {#each messages as message, idx (message.id)}
          {@const isLast = idx === messages.length - 1}
          <div class="mx-auto flex w-full max-w-[71ch] flex-col gap-3">
            {#if message.role === "user"}
              <div
                in:fly={{ duration: 500, y: 60 }}
                class="prose bg-secondary max-w-full self-end rounded-3xl rounded-br-none px-5 py-3 break-words md:max-w-[85%]"
              >
                <p class="m-0 text-[0.9375rem] leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            {:else}
              <div class="relative pt-3 text-[0.9375rem] leading-relaxed">
                {#if message.content}
                  <Markdown source={message.content} />
                {/if}
                {#if isStreaming && isLast && !message.content}
                  <div class="flex items-center gap-2 py-1.5" role="status" aria-label={m.assistant_is_typing()}>
                    <span class="typing-dot"></span>
                    <span class="typing-dot" style="animation-delay: 700ms"></span>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {:else}
      <div class="flex flex-grow flex-col items-center justify-center px-4">
        <div class="flex flex-col items-center gap-3 text-center">
          {#if data.assistant.icon_id}
            <img
              src="{data.baseUrl}/api/v1/icons/{data.assistant.icon_id}/"
              alt=""
              class="h-14 w-14 rounded-xl object-cover shadow-sm"
            />
          {/if}
          <div>
            <p class="text-primary text-sm font-semibold">{data.assistant.name}</p>
            {#if data.assistant.description}
              <p class="text-muted mt-1 max-w-[36ch] text-xs leading-relaxed">{data.assistant.description}</p>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Input area -->
  <div class="flex flex-col items-center gap-1 bg-gradient-to-b from-transparent to-[var(--background-primary)] px-2.5 pt-0 pb-1.5 md:px-4">
    <form
      class="border-default bg-primary ring-dimmer relative flex w-full max-w-[74ch] flex-col rounded-xl border p-1 shadow-md ring-offset-0 transition-all duration-300 focus-within:border-stronger hover:border-stronger focus-within:shadow-lg hover:ring-4"
      onsubmit={(e) => { e.preventDefault(); sendMessage(); }}
    >
      <textarea
        bind:this={textareaEl}
        class="text-primary placeholder:text-muted w-full resize-none bg-transparent px-3 py-2 text-sm leading-relaxed focus:outline-none"
        placeholder={m.public_chat_placeholder()}
        rows={1}
        bind:value={input}
        onkeydown={handleKeydown}
        oninput={autoResize}
      ></textarea>

      <div class="flex justify-end">
        {#if isStreaming}
          <button
            type="button"
            aria-label={m.cancel_your_request()}
            onclick={() => abortController?.abort("User cancelled")}
            class="bg-secondary hover:bg-hover-stronger flex h-8 items-center justify-center gap-1 rounded-lg pr-1 pl-2 text-sm transition-colors"
          >
            {m.stop_answer()}
            <IconStopCircle />
          </button>
        {:else}
          <button
            disabled={isAskingDisabled}
            aria-label={m.submit_your_question()}
            type="submit"
            class="bg-secondary hover:bg-hover-stronger disabled:bg-tertiary disabled:text-secondary flex h-8 items-center justify-center gap-1 rounded-lg pr-1 pl-2 text-sm transition-colors"
          >
            {m.send()}
            <IconEnter />
          </button>
        {/if}
      </div>
    </form>

    <div class="flex items-center justify-center pb-0.5 opacity-30">
      <EneoWordMark class="text-brand-intric h-3 w-12" />
    </div>
  </div>
</div>

<style lang="postcss">
  @reference "@intric/ui/styles";

  .embed-container {
    background: var(--background-primary);
    margin: 0;
    padding: 0;
  }

  @keyframes typing-breathe {
    0%,
    100% {
      transform: scale(1) translateX(0);
      opacity: 0.5;
    }
    50% {
      transform: scale(1.15) translateX(2px);
      opacity: 1;
    }
  }

  .typing-dot {
    @apply bg-accent-stronger h-2 w-2 rounded-full;
    animation: typing-breathe 1.4s ease-in-out infinite;
  }

  @media (prefers-reduced-motion: reduce) {
    .typing-dot {
      animation: none;
      opacity: 0.7;
    }
  }
</style>
