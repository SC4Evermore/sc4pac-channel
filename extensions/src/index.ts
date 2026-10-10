import {Sc4PacPlugin} from "./modules/sc4pac/sc4-pac-plugin/sc4-pac-plugin";
import {getIdFromUrl, h} from "./modules/sc4pac/utils";
import type {Sc4PacPluginOptions} from "./modules/sc4pac/sc4-pac-plugin/sc4-pac-plugin-options";

async function setup(options: Sc4PacPluginOptions | string[]) {
  if (Array.isArray(options)) {
    options = {channels: options};
  }
  const plugin = new Sc4PacPlugin(options);
  await plugin.setup();
  return {plugin, h};
}

const channel = 'sc4evermore.github.io/sc4pac-channel/channel';
setup([channel]).then(({plugin, h}) => {
  let id = getIdFromUrl();

  if (!id) return;
  let packages = plugin.find('sc4e', id);
  if (packages.length === 0) return;

  packages.sort((a, b) => {
    let ai = a.channelUrl.includes(channel) ? 1 : -1;
    let bi = b.channelUrl.includes(channel) ? 1 : -1;
    return ai - bi;
  });

  const map = new Map();
  for (let pkg of packages) {
    map.set(pkg.id, pkg)
  }
  packages = [...map.values()];
  
  const button = h('a', {
    href: plugin.getInstallUrl(packages, {provider: 'sc4e', id}),
    id: 'install-sc4pac',
    class: 'jdbutton jblack'
  }, ['Download with SC4Pac']);


  const a = [...document.querySelectorAll('a.jdbutton')].find(a => {
    const href = a.getAttribute('href');
    if (!href) return false;
    try {
      let url = new URL(href, 'https://www.sc4evermore.com/');
      return url.searchParams.get('task') === 'download.send'
    } catch {
      return false;
    }
  });

  if (!a) {
    return;
  }

  const li = h('li', {}, [button]);
  const ul = a.closest('ul');
  ul?.appendChild(li);

  // add normal link too
  ul?.appendChild(h('li', {
    style: 'text-align: center',
  }, [
    h('a', {
      href: plugin.getViewUrl(packages),
      target: '_blank',
      style: 'text-decoration: underline; font-size: 8pt',
    }, ['View on sc4pac website'])
  ]));
});