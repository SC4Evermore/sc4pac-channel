import {Package} from '../package/package';
import type {ChannelData} from "../channel/channel-data";
import type {Sc4PacPluginOptions} from "./sc4-pac-plugin-options";
import {ready} from "../utils";

const CACHE_HEADER = 'X-Cached-Date';
const CACHE_MINUTES = 30;

/**
 * Represents the main sc4-pac-plugin interface. This is responsible for loading the correct channels, etc.
 */
export class Sc4PacPlugin {
  readonly channels: string[] = [];
  readonly cacheMinutes: number = CACHE_MINUTES;
  readonly index: Record<string, Record<string, Package[]>> = {};

  constructor(options: Sc4PacPluginOptions) {
    const {channels, cacheMinutes} = options;
    this.channels = [...channels];
    this.cacheMinutes = cacheMinutes || CACHE_MINUTES;
  }

  find(exchangeId: string, externalId: string) {
    return this.index[exchangeId]?.[externalId] ?? [];
  }

  install(sc4Package: Package) {
    const url = this.getInstallUrl(sc4Package);
    window.open(url);
  }

  /**
   * Returns the installation url for the package, or array of packages.
   *
   * @param pkg the package(s) to pass in
   * @param external if given and there are 2+ packages, the short `externalId` url format is used to stay under the
   * Windows URL length limit
   * @returns the sc4pac:/// protocol url
   */
  getInstallUrl(pkg: Package | Package[], external?: {provider: string; id: string}): string {
    const packages = [pkg].flat();
    const channels = new Set<string>();
    const url = new URL('sc4pac:///package');
    if (external && packages.length >= 2) {
      url.searchParams.append('externalId', external.id);
      url.searchParams.append('externalIdProvider', external.provider);
      packages.forEach(p => channels.add(p.channelUrl));
    } else {
      for (let pkg of packages) {
        url.searchParams.append('pkg', pkg.id);
        channels.add(pkg.channelUrl);
      }
    }
    for (let channel of channels) {
      url.searchParams.append('channel', channel);
    }
    return url.toString();
  }

  /**
   * Returns the "view on sc4pac website" url for the given package(s). If an url is not returned, we default to the
   * SC4pac homepage.
   * @param pkg the package(s) to pass in
   * @returns the view URL
   */
  getViewUrl(pkg: Package | Package[]): string {
    const [first] = [pkg].flat();
    return first?.getViewUrl() ?? 'https://memo33.github.io/sc4pac/#/';
  }

  async setup() {
    await Promise.all([
      ready(),
      this.loadChannel('memo33.github.io/sc4pac/channel'),
      ...this.channels.map(channel => this.loadChannel(channel))
    ])
  }

  async fetchWithCache(url: string): Promise<Response> {
    const cacheName = 'sc4pac-channels';
    const cache = await window.caches.open(cacheName);
    const cachedResponse = await cache.match(url);

    if (cachedResponse) {
      const dateHeader = cachedResponse.headers.get(CACHE_HEADER);
      if (dateHeader) {
        const cachedDate = new Date(dateHeader);
        const now = Date.now();
        const elapsed = (now - cachedDate.getTime()) / (1000 * 60);
        if (elapsed < this.cacheMinutes) {
          return cachedResponse;
        }
      }
    }

    const networkResponse = await fetch(url);
    const responseToCache = networkResponse.clone();

    const updatedHeaders = new Headers(responseToCache.headers);
    updatedHeaders.set(CACHE_HEADER, new Date().toISOString());

    const modifiedResponse = new Response(responseToCache.body, {
      status: responseToCache.status,
      statusText: responseToCache.statusText,
      headers: updatedHeaders,
    });

    await cache.put(url, modifiedResponse);
    return networkResponse;
  }

  /**
   * Loads a specific channel.
   * @param channel
   */
  async loadChannel(channel: string) {
    const {index} = this;
    const url = `https://${channel}/sc4pac-channel-contents.json`;
    const response: Response = await this.fetchWithCache(url);
    const json: ChannelData = await response.json();
    for (let pkg of json.packages) {
      const externalIds = pkg.externalIds || {};
      for (let [exchangeId, ids] of Object.entries(externalIds)) {
        const exchange: Record<string, Package[]> = index[exchangeId] ??= {};
        for (let id of ids) {
          const arr = exchange[id] ??= [];
          arr.push(new Package({
            channelUrl: `https://${channel}`,
            ...pkg,
          }))
        }

      }
    }
  }
}