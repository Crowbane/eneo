<script lang="ts">
  import AssistantActions from "./AssistantActions.svelte";
  import { getSpacesManager } from "$lib/features/spaces/SpacesManager";
  import { dynamicColour } from "$lib/core/colours";
  import GroupChatActions from "./GroupChatActions.svelte";
  import type { AssistantSparse, GroupChatSparse } from "@intric/intric-js";
  import { getChatQueryParams } from "$lib/features/chat/getChatQueryParams";
  import { getAppContext } from "$lib/core/AppContext";

  export let item: AssistantSparse | GroupChatSparse;

  const { environment } = getAppContext();
  const {
    state: { currentSpace }
  } = getSpacesManager();

  // Generate icon URL from icon_id
  $: iconUrl = item.icon_id
    ? `${environment.baseUrl}/api/v1/icons/${item.icon_id}/`
    : null;

  // Public sharing flag (field exists at runtime but not yet in generated types)
  $: isPubliclyShared = item.type === "assistant" && !!(item as any).public_sharing_enabled;
</script>

<a
  aria-label={item.name}
  {...dynamicColour({ basedOn: item.id })}
  href="/spaces/{$currentSpace.routeId}/chat/?{getChatQueryParams({
    chatPartner: item,
    tab: 'chat'
  })}"
  class="group border-dynamic-default bg-dynamic-dimmer text-dynamic-stronger hover:bg-dynamic-default hover:text-on-fill relative flex aspect-square flex-col items-start gap-2 border-t p-2 px-4"
>
  <h2 class="line-clamp-2 pt-1 font-mono text-sm">
    {item.name}
  </h2>

  <div class="hover:text-primary absolute right-2 bottom-2">
    {#if item.type === "assistant"}
      <AssistantActions assistant={item}></AssistantActions>
    {:else if item.type === "group-chat"}
      <GroupChatActions groupChat={item}></GroupChatActions>
    {/if}
  </div>

  <span
    class="group-hover:text-on-fill pointer-events-none absolute inset-0 flex items-center justify-center font-mono text-[4.5rem]"
  >
    {#if iconUrl}
      <div class="relative flex h-32 w-32 items-center justify-center overflow-hidden rounded-xl">
        <img src={iconUrl} alt={item.name} class="h-full w-full object-cover" />
        {#if item.type === "group-chat"}
          <div class="absolute -right-1 -bottom-1 flex h-8 w-8 items-center justify-center rounded-full border border-current bg-white/80 text-inherit backdrop-blur-sm dark:bg-black/60">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
            </svg>
          </div>
        {/if}
      </div>
    {:else if item.type === "group-chat"}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
        class="size-20"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z"
        />
      </svg>
    {:else}
      {([...item.name][0] ?? "").toUpperCase()}
    {/if}</span
  >

  <div class="flex-grow"></div>

  {#if isPubliclyShared}
    <div class="absolute bottom-2 left-2 flex h-5 w-5 items-center justify-center rounded-full bg-white/60 backdrop-blur-sm dark:bg-black/40" title="Publicly shared">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-3.5 w-3.5 opacity-70">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A8.966 8.966 0 0 1 3 12c0-1.264.26-2.467.732-3.558" />
      </svg>
    </div>
  {/if}
</a>
