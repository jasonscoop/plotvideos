import STYLES_CSS from "./static/styles.css";
import LANG_DROPDOWN_JS from "./static/lang-dropdown.client.js";
import WATCH_PAGE_JS from "./static/watch-page.client.js";

function shortHash(src: string): string {
  let h = 0;
  for (let i = 0; i < src.length; i++) h = (Math.imul(31, h) + src.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

export const ASSET_HASHES = {
  css: shortHash(STYLES_CSS),
  langDropdown: shortHash(LANG_DROPDOWN_JS),
  watchPage: shortHash(WATCH_PAGE_JS),
};
