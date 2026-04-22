/**
 * Request pipeline:
 *   orflaedi.is/*  → 301 redirect to https://www.orflaedi.is/<path>
 *   www.orflaedi.is/*, *.workers.dev/* → static assets
 */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === "orflaedi.is") {
      url.hostname = "www.orflaedi.is";
      return Response.redirect(url.toString(), 301);
    }
    return env.ASSETS.fetch(request);
  },
};
