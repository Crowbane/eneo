import type { RequestHandler } from "./$types";

export const GET: RequestHandler = ({ params, url }) => {
  const token = params.token;
  const embedUrl = `${url.origin}/shared/assistant/${token}/embed`;

  const script = `
(function() {
  if (document.getElementById('eneo-chat-widget')) return;

  var btn = document.createElement('button');
  btn.id = 'eneo-chat-widget-btn';
  btn.setAttribute('aria-label', 'Open chat');
  btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="28" height="28"><path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"/></svg>';
  Object.assign(btn.style, {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    background: '#055594',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    zIndex: '999999',
    transition: 'transform 0.2s'
  });
  btn.onmouseenter = function() { btn.style.transform = 'scale(1.1)'; };
  btn.onmouseleave = function() { btn.style.transform = 'scale(1)'; };

  var container = document.createElement('div');
  container.id = 'eneo-chat-widget';
  container.style.cssText = 'position:fixed;bottom:88px;right:20px;width:400px;height:600px;z-index:999998;display:none;border-radius:12px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,0.12);transition:opacity 0.2s,transform 0.2s;opacity:0;transform:translateY(10px);';

  var iframe = document.createElement('iframe');
  iframe.src = '${embedUrl}';
  iframe.style.cssText = 'width:100%;height:100%;border:none;';
  iframe.setAttribute('title', 'Chat');
  container.appendChild(iframe);

  var open = false;
  btn.onclick = function() {
    open = !open;
    if (open) {
      container.style.display = 'block';
      requestAnimationFrame(function() {
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
      });
    } else {
      container.style.opacity = '0';
      container.style.transform = 'translateY(10px)';
      setTimeout(function() { container.style.display = 'none'; }, 200);
    }
  };

  document.body.appendChild(container);
  document.body.appendChild(btn);
})();
`;

  return new Response(script, {
    headers: {
      "Content-Type": "application/javascript",
      "Cache-Control": "public, max-age=3600",
      "Access-Control-Allow-Origin": "*"
    }
  });
};
