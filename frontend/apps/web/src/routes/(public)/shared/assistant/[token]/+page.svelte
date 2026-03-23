<script lang="ts">
  import { tick } from "svelte";
  import { fade, fly } from "svelte/transition";
  import { Markdown } from "@intric/ui";
  import EneoWordMark from "$lib/assets/EneoWordMark.svelte";
  import { IconEnter } from "@intric/icons/enter";
  import { IconStopCircle } from "@intric/icons/stop-circle";
  import { IconArrowDownToLine } from "@intric/icons/arrow-down-to-line";
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
  let showScrollToBottom = $state(false);
  let abortController: AbortController | undefined;
  let textareaEl: HTMLTextAreaElement | undefined = $state();

  function handleScroll() {
    if (!scrollContainer) return;
    const bottomThreshold = 150;
    const distanceFromBottom =
      scrollContainer.scrollHeight - scrollContainer.clientHeight - scrollContainer.scrollTop;
    showScrollToBottom = distanceFromBottom > bottomThreshold;
  }

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
    textareaEl.style.height = Math.min(textareaEl.scrollHeight, 200) + "px";
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

    try {
      const res = await fetch(
        `${data.baseUrl}/api/v1/public/assistants/${data.token}/ask/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream"
          },
          body: JSON.stringify({ question, stream: true }),
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

<div class="mx-auto flex h-full w-full max-w-[960px] flex-col p-0 md:px-4 md:py-3">
  <div
    class="chat-container relative flex min-h-0 flex-1 flex-col overflow-hidden md:rounded-sm"
  >
    <!-- Header -->
    <header class="border-default z-10 flex items-center gap-3 border-b px-4 py-3 md:px-6 md:py-4">
      {#if data.assistant.icon_id}
        <img
          src="{data.baseUrl}/api/v1/icons/{data.assistant.icon_id}/"
          alt=""
          class="h-10 w-10 shrink-0 rounded-lg object-cover"
        />
      {/if}
      <div class="min-w-0 flex-1">
        <h1 class="text-primary truncate text-lg font-semibold">{data.assistant.name}</h1>
        {#if data.assistant.description}
          <p class="text-muted truncate text-sm">{data.assistant.description}</p>
        {/if}
      </div>
      <a href="/" class="shrink-0 opacity-60 transition-opacity hover:opacity-100" aria-label="Eneo">
        <EneoWordMark class="text-brand-intric h-5 w-20" />
      </a>
    </header>

    <!-- Scrollable message area -->
    <div
      class="relative flex min-h-0 flex-1 flex-col overflow-y-auto"
      bind:this={scrollContainer}
      onscroll={handleScroll}
    >
      {#if messages.length > 0}
        <div
          class="flex flex-grow flex-col gap-2 p-4 md:p-8"
          aria-live="polite"
        >
          {#each messages as message, idx (message.id)}
            {@const isLast = idx === messages.length - 1}
            <div class="mx-auto flex w-full max-w-[71ch] flex-col gap-4">
              {#if message.role === "user"}
                <div
                  in:fly={{ duration: 700, y: 100 }}
                  class="prose bg-secondary max-w-full self-end rounded-3xl rounded-br-none px-8 py-4 break-words md:max-w-[85%]"
                >
                  <p class="m-0 text-lg whitespace-pre-wrap">{message.content}</p>
                </div>
              {:else}
                <div class="relative pt-4 text-lg">
                  {#if message.content}
                    <Markdown source={message.content} />
                  {/if}
                  {#if isStreaming && isLast && !message.content}
                    <div class="flex items-center gap-2 py-2" role="status" aria-label={m.assistant_is_typing()}>
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
          <div class="flex max-w-[50ch] flex-col items-center gap-5 text-center">
            {#if data.assistant.icon_id}
              <img
                src="{data.baseUrl}/api/v1/icons/{data.assistant.icon_id}/"
                alt=""
                class="h-20 w-20 rounded-xl object-cover shadow-sm"
              />
            {/if}
            <div>
              <h2 class="text-primary text-xl font-semibold">{data.assistant.name}</h2>
              {#if data.assistant.description}
                <div class="text-secondary mt-2">
                  <Markdown
                    class="*:m-0 [&_p]:text-center"
                    source={data.assistant.description}
                  />
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Input area (outside scroll container) -->
    <div
      class="relative flex flex-col items-center gap-3 border-t border-transparent px-2 pt-2 pb-4 md:gap-4 md:px-6 md:pb-6"
    >
      {#if showScrollToBottom}
        <div transition:fade={{ duration: 150 }} class="absolute -top-12 left-1/2 -translate-x-1/2">
          <button
            class="border-stronger bg-primary ring-default hover:bg-secondary flex gap-1 rounded-full border px-1.5 py-1.5 shadow-lg ring-offset-0 hover:ring-2"
            onclick={scrollToBottom}
            aria-label={m.scroll_to_bottom()}
          >
            <IconArrowDownToLine />
          </button>
        </div>
      {/if}

      <form
        class="border-default bg-primary ring-dimmer relative flex w-full max-w-[74ch] flex-col rounded-xl border p-1.5 shadow-md ring-offset-0 transition-all duration-300 focus-within:border-stronger hover:border-stronger focus-within:shadow-lg hover:ring-4"
        onsubmit={(e) => { e.preventDefault(); sendMessage(); }}
      >
        <textarea
          bind:this={textareaEl}
          class="text-primary placeholder:text-muted w-full resize-none bg-transparent px-3 py-2.5 text-base leading-relaxed focus:outline-none"
          placeholder={m.public_chat_placeholder()}
          rows={1}
          bind:value={input}
          onkeydown={handleKeydown}
          oninput={autoResize}
        ></textarea>

        <div class="mt-1 flex justify-end">
          {#if isStreaming}
            <button
              type="button"
              aria-label={m.cancel_your_request()}
              onclick={() => abortController?.abort("User cancelled")}
              class="bg-secondary hover:bg-hover-stronger flex h-9 items-center justify-center gap-1 rounded-lg pr-1 pl-2 transition-colors"
            >
              {m.stop_answer()}
              <IconStopCircle />
            </button>
          {:else}
            <button
              disabled={isAskingDisabled}
              aria-label={m.submit_your_question()}
              type="submit"
              class="bg-secondary hover:bg-hover-stronger disabled:bg-tertiary disabled:text-secondary flex h-9 items-center justify-center gap-1 rounded-lg pr-1 pl-2 transition-colors"
            >
              {m.send()}
              <IconEnter />
            </button>
          {/if}
        </div>
      </form>

      <div class="flex items-center justify-center pt-1 opacity-40">
        <EneoWordMark class="text-brand-intric h-4 w-16" />
      </div>
    </div>
  </div>
</div>

<style lang="postcss">
  @reference "@intric/ui/styles";

  .chat-container {
    background: var(--background-primary);
    border: 0.5px solid var(--border-stronger);
    box-shadow:
      0px 18px 12px 2px rgba(0, 0, 0, 0.12),
      0px 0px 14px 2px rgba(0, 0, 0, 0.09);
  }

  @media (max-width: 767px) {
    .chat-container {
      border-left: 0;
      border-right: 0;
      border-bottom: 0;
      border-radius: 0;
    }
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
