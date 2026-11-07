# sc4pac-channel
Metadata channel for [sc4pac](https://memo33.github.io/sc4pac/#/) that automatically adds compatible SC4E uploads.

## Testing changes
Content added to this channel should be tested according to the structures outlined in [Testing your changes](https://memo33.github.io/sc4pac/#/metadata?id=testing-your-changes). Individual files may be added directly to the sc4pac GUI with the `file:///` syntax, or if multiple files will be updated, you may build the channel and add the entire local channel to the CLI or GUI. For example build the channel to, 
``` sh
sc4pac channel build --output "C:/path/to/this/repo/sc4e-channel/dist/channel/json/" C:/path/to/this/repo/sc4e-channel/src/yaml/
```
and then add `file:///C:/path/to/this/repo/sc4e-channel/src/yaml/` in the list of sc4pac channels.

Also, if you are testing files with lots of variants or complex logic, the [`sc4pac test`](https://memo33.github.io/sc4pac/#/cli?id=test) command is very helpful.
