import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";

export const load = async ({ params, fetch }) => {
  const baseUrl = env.PUBLIC_ENEO_BACKEND_URL || env.PUBLIC_INTRIC_BACKEND_URL || "";
  const res = await fetch(`${baseUrl}/api/v1/public/assistants/${params.token}/`);

  if (!res.ok) {
    throw error(404);
  }

  const assistant = await res.json();

  return {
    token: params.token,
    assistant,
    baseUrl
  };
};
