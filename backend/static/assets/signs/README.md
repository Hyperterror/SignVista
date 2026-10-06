# Sign demonstration media

The API serves files in this folder at `/assets/signs/...`.

Add one GIF (or short looping WebP) per sign, named after the vocabulary key:

- `hello.gif`, `thank_you.gif`, `how_are_you.gif`, `help.gif`, `water.gif`, `food.gif`,
  `yes.gif`, `no.gif`, `good.gif`, `bad.gif`, `sorry.gif`, `please.gif`, `name.gif`,
  `family.gif`, `friend.gif`
- `alphabet/a.gif` … `alphabet/z.gif`

Until a file exists, the API returns an empty `gif_url` and the frontend shows
the written description instead of a broken image.

Use only recordings you have the rights to (ideally made by fluent ISL signers).
