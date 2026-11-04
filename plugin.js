// Fusión Vegitto y Gogeta — temas de toda la app (appThemes, apiVersion 18) + pantalla de presentación.
// No usa la red: el manifiesto declara "hosts": []. Kino dibuja la pantalla; aquí solo se describe el árbol.

const THEMES = [
  {
    id: "vegitto",
    icon: "bolt",
    name: "Vegitto Azul",
    nameEn: "Blue Vegitto",
    tag: "Gi azul casi negro, pelo cian y faja naranja.",
    tagEn: "Near-black blue gi, cyan hair and an orange sash.",
    notes: [
      ["Mechón de pelo SSJ Blue pegado a la «k»", "SSJ Blue hair tuft stuck to the «k»"],
      ["La «i» con aro, la «o» partida en cian y oro y la barra bicolor", "The «i» with a ring, the «o» split in cyan and gold, and the two-tone bar"],
    ],
    notesEn: [
      ["SSJ Blue hair tuft stuck to the «k»", "SSJ Blue hair tuft stuck to the «k»"],
      ["The «i» with a ring, the «o» split in cyan and gold, and the two-tone bar", "The «i» with a ring, the «o» split in cyan and gold, and the two-tone bar"],
    ],
  },
  {
    id: "gogeta",
    icon: "bolt",
    name: "Gogeta Fuego",
    nameEn: "Fire Gogeta",
    tag: "Chaleco naranja, ropa clara, faja azul y botas doradas.",
    tagEn: "Orange vest, light clothes, blue sash and gold boots.",
    notes: [
      ["Mechón de pelo naranja pegado a la «k»", "Orange hair tuft stuck to the «k»"],
      ["La «i» con aro azul, la «o» partida en naranja y azul y la barra bicolor", "The «i» with a blue ring, the «o» split in orange and blue, and the two-tone bar"],
    ],
    notesEn: [
      ["Orange hair tuft stuck to the «k»", "Orange hair tuft stuck to the «k»"],
      ["The «i» with a blue ring, the «o» split in orange and blue, and the two-tone bar", "The «i» with a blue ring, the «o» split in orange and blue, and the two-tone bar"],
    ],
  },
  {
    id: "fusion",
    icon: "magic",
    name: "Fusión V+G",
    nameEn: "V+G Fusion",
    tag: "Los dos a la vez: oro y cian con el azul de la faja.",
    tagEn: "Both at once: gold and cyan with the sash's blue.",
    notes: [
      ["Mechón bicolor pegado a la «k»", "Two-tone hair tuft stuck to the «k»"],
      ["La «o» partida en azul y naranja y la barra bicolor", "The «o» split in blue and orange, and the two-tone bar"],
    ],
    notesEn: [
      ["Two-tone hair tuft stuck to the «k»", "Two-tone hair tuft stuck to the «k»"],
      ["The «o» split in blue and orange, and the two-tone bar", "The «o» split in blue and orange, and the two-tone bar"],
    ],
  },
];

const t = (es, en, extra) => Object.assign({ type: "Text", text: es, textEn: en }, extra || {});

function themeCard(theme, active, en) {
  const header = [
    { type: "Icon", name: theme.icon, color: "primary" },
    {
      type: "Column",
      gap: 4,
      children: [
        {
          type: "Row",
          wrap: true,
          gap: 8,
          children: [
            t(theme.name, theme.nameEn, { style: "h3" }),
            active
              ? { type: "Badge", text: "Activo", textEn: "On" }
              : { type: "Badge", text: "Gratis", textEn: "Free", color: "surfaceVariant" },
          ],
        },
        t(theme.tag, theme.tagEn, { color: "muted", style: "caption" }),
      ],
    },
  ];

  const bullets = (en ? theme.notesEn : theme.notes).map((line) => ({
    type: "Row",
    gap: 8,
    children: [
      { type: "Icon", name: "check", color: "primary" },
      t(line[0], line[1], { style: "caption", color: "muted" }),
    ],
  }));

  const action = active
    ? {
        type: "Button",
        variant: "secondary",
        icon: "refresh",
        labelText: "Volver al tema de Kino",
        labelTextEn: "Back to Kino's theme",
        onPressed: { go: { useTheme: { theme: null } } },
      }
    : {
        type: "ElevatedButton",
        icon: "check",
        labelText: "Usar este tema",
        labelTextEn: "Use this theme",
        onPressed: { go: { useTheme: { theme: theme.id } } },
      };

  return {
    type: "Card",
    key: "theme-" + theme.id,
    variant: active ? "filled" : "outlined",
    children: [
      { type: "Row", gap: 12, children: header },
      { type: "Column", gap: 8, children: bullets },
      { type: "Row", wrap: true, gap: 8, children: [action] },
    ],
  };
}

export async function screen({ activeTheme, lang }) {
  const en = lang === "en";
  const active = typeof activeTheme === "string" ? activeTheme : null;

  return {
    type: "SingleChildScrollView",
    padding: { compact: 16, expanded: 24 },
    children: [{
      type: "Column",
      gap: 16,
      children: [
        {
          type: "Card",
          key: "intro",
          variant: "filled",
          children: [
            {
              type: "Row",
              gap: 12,
              children: [
                { type: "Icon", name: "magic", color: "primary" },
                {
                  type: "Column",
                  gap: 4,
                  children: [
                    t("Vegitto & Gogeta", "Vegitto & Gogeta", { style: "h1" }),
                    t("Tres temas de fusión para toda la app", "Three fusion themes for the whole app", { color: "muted" }),
                  ],
                },
              ],
            },
            t(
              "Colores, fondo degradado, bordes redondeados, sombras y controles del reproductor, en el celular y en el TV. El logo de Kino se queda, con el mechón de pelo y los colores de cada personaje.",
              "Colors, gradient background, rounded corners, shadows and player controls, on phone and TV. Kino's logo stays, with each character's hair tuft and colors.",
              { color: "muted" }
            ),
          ],
        },
        ...THEMES.map((theme) => themeCard(theme, theme.id === active, en)),
        {
          type: "Card",
          key: "customize",
          variant: "plain",
          children: [
            t("Ajustes ▸ Apariencia", "Settings ▸ Appearance", { style: "h4" }),
            t(
              "Ahí se cambia de tema y «Personalizar» deja tocar el acento, el foco, las esquinas y el tamaño del texto, con muestras pensadas para el control remoto.",
              "There you switch themes, and “Customize” lets you tune the accent, focus, corners and text size, with swatches made for the remote.",
              { color: "muted" }
            ),
            { type: "Divider" },
            t(
              "Necesita Kino 0.9.81 o posterior. No se conecta a internet.",
              "Needs Kino 0.9.81 or later. It doesn't connect to the internet.",
              { style: "caption", color: "muted" }
            ),
          ],
        },
      ],
    }],
  };
}

// Los botones llevan su propia acción `go.useTheme`, así que no hay eventos que atender.
export async function screenEvent() {
  return null;
}
