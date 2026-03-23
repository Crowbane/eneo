<script lang="ts">
  import { Button, Input, Tooltip } from "@intric/ui";
  import { IconLoadingSpinner } from "@intric/icons/loading-spinner";
  import { m } from "$lib/paraglide/messages";
  import { toast } from "$lib/components/toast";
  import { page } from "$app/state";

  type Props = {
    assistant: {
      id: string;
      name: string;
      published: boolean;
      public_sharing_enabled: boolean;
      public_sharing_token: string | null;
    };
    endpoints: {
      enablePublicSharing: (assistant: { id: string }) => Promise<any>;
      disablePublicSharing: (assistant: { id: string }) => Promise<any>;
    };
    hasUnsavedChanges: boolean;
  };

  let { assistant = $bindable(), endpoints, hasUnsavedChanges }: Props = $props();

  let isLoading = $state(false);
  let sharingEnabled = $state(assistant.public_sharing_enabled);
  let copied = $state<"link" | "iframe" | "js" | null>(null);
  let activeTab = $state<"link" | "iframe" | "js">("link");

  $effect(() => {
    sharingEnabled = assistant.public_sharing_enabled;
  });

  const publicUrl = $derived(
    assistant.public_sharing_token
      ? `${page.url.origin}/shared/assistant/${assistant.public_sharing_token}`
      : ""
  );

  const iframeCode = $derived(
    `<iframe src="${publicUrl}/embed" width="400" height="600" frameborder="0" style="border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"></iframe>`
  );

  const jsCode = $derived(
    `<script src="${publicUrl}/widget.js"><\/script>`
  );

  async function handleToggle(params: { current: boolean; next: boolean }) {
    const enable = params.next;
    isLoading = true;
    try {
      if (enable) {
        assistant = await endpoints.enablePublicSharing(assistant);
      } else {
        assistant = await endpoints.disablePublicSharing(assistant);
      }
    } catch (e) {
      sharingEnabled = params.current;
      toast.error(
        enable ? m.public_sharing_enabled() : m.public_sharing_disabled()
      );
    }
    isLoading = false;
  }

  function copyToClipboard(text: string, type: "link" | "iframe" | "js") {
    navigator.clipboard.writeText(text);
    copied = type;
    setTimeout(() => {
      copied = null;
    }, 2000);
  }
</script>

<div class="border-default border-b py-3 px-2">
  <div class="flex items-center gap-3">
    {#if isLoading}
      <div class="text-muted flex flex-grow items-center gap-2">
        <IconLoadingSpinner class="animate-spin h-4 w-4"></IconLoadingSpinner>
        <span class="text-sm">{m.updating()}</span>
      </div>
    {:else}
      <Tooltip
        text={!assistant.published
          ? m.publish_first_for_public_sharing()
          : hasUnsavedChanges
            ? m.save_or_discard_changes_before_updating()
            : undefined}
        class="w-full"
      >
        <Input.Switch
          value={sharingEnabled}
          sideEffect={handleToggle}
          disabled={!assistant.published || hasUnsavedChanges || isLoading}
        >
          <span class="text-sm">{m.public_sharing()}</span>
        </Input.Switch>
      </Tooltip>
    {/if}
  </div>

  {#if assistant.public_sharing_enabled && assistant.public_sharing_token}
    <div class="mt-3 flex flex-col gap-2">
      <!-- Link -->
      <div class="bg-secondary rounded-lg p-3">
        <div class="text-muted mb-1.5 text-xs font-medium">{m.public_link()}</div>
        <div class="flex items-center gap-2">
          <code class="text-primary flex-1 overflow-x-auto text-xs break-all">{publicUrl}</code>
          <Button
            variant="outlined"
            on:click={() => copyToClipboard(publicUrl, "link")}
          >
            {copied === "link" ? m.public_link_copied() : m.copy_public_link()}
          </Button>
        </div>
      </div>

      <!-- Embed iframe -->
      <div class="bg-secondary rounded-lg p-3">
        <div class="text-muted mb-1.5 text-xs font-medium">{m.embed_iframe()}</div>
        <div class="flex items-center gap-2">
          <code class="text-primary flex-1 overflow-x-auto text-xs break-all">{iframeCode}</code>
          <Button
            variant="outlined"
            on:click={() => copyToClipboard(iframeCode, "iframe")}
          >
            {copied === "iframe" ? m.embed_code_copied() : m.copy_embed_code()}
          </Button>
        </div>
      </div>

      <!-- Embed JavaScript -->
      <div class="bg-secondary rounded-lg p-3">
        <div class="text-muted mb-1.5 text-xs font-medium">{m.embed_javascript()}</div>
        <div class="flex items-center gap-2">
          <code class="text-primary flex-1 overflow-x-auto text-xs break-all">{jsCode}</code>
          <Button
            variant="outlined"
            on:click={() => copyToClipboard(jsCode, "js")}
          >
            {copied === "js" ? m.embed_code_copied() : m.copy_embed_code()}
          </Button>
        </div>
      </div>
    </div>
  {/if}
</div>
