# Spec 01 — Sistema "Amplo & Blocado"

> Define o sistema de layout do redesign. Consome `src/style.css` (tokens) sem
> alterá-lo. Adiciona utilitários de grid/gutter e três primitivas novas.

## 1. Princípios

1. **Full-bleed por padrão na estrutura, `.measure` só na prosa.** A coluna
   `max-w-6xl` centralizada deixa de ser o default. A largura útil passa a ser o
   viewport com gutter; prosa longa continua limitada a 70ch dentro da célula.
2. **Sem bordas, sem linhas, sem cards.** Os blocos NÃO têm divisória visível.
   O que separa um bloco do outro é **espaço em branco generoso + alinhamento em
   grid + troca de superfície**. Nada de `gap-px bg-border`, hairline, moldura,
   card arredondado. Ver `refs/1.png` e `refs/3.png`: blocos hard-edge num campo
   uniforme, sem nenhuma linha.
3. **Grade invisível (só alinhamento).** Existe um grid modular para alinhar os
   blocos, mas ele **não é renderizado**. Células podem ficar vazias de propósito
   (o vazio é ritmo e elegância, como em `refs/1.png`).
4. **O dado e a manchete mandam.** Tipografia display (Thin) e número (mono)
   são os elementos estruturais, não ornamento. Foto entra como bloco de borda
   dura (hard-edge), sem radius nem moldura.
5. **Big number como âncora de impacto.** Onde houver número, ele é grande e
   protagonista (mono, clamp ~2.5→5rem ou maior), com a unidade no label e a
   fonte no popover. Número curto (mover unidade pro label). Padrão: `DataPoint`
   com `numberClassName`.
6. **Heading de impacto, texto ao mínimo.** Heading display bem definida, com
   forte contraste de peso (Thin ↔ Bold), carrega a mensagem. Corpo só quando
   indispensável e curtíssimo; preferir cortar a explicar. O mínimo possível de
   texto por bloco.

## 2. Largura e gutter (novos utilitários)

Adicionar a `src/style.css` (camada `@theme inline` / `@layer base`), sem mexer
em tokens existentes:

```css
@theme inline {
  --gutter: clamp(1rem, 4vw, 4rem);   /* respiro lateral do full-bleed */
  --block-max: 120rem;                 /* teto de largura do conteúdo amplo */
}
```

| Container | Uso | Regra |
| --- | --- | --- |
| Full-bleed | mídia, faixas de cor, grade de fundo | `width: 100%` da section, sem max-width |
| Wide | conteúdo amplo (grids blocados) | `max-w-[var(--block-max)] mx-auto px-[var(--gutter)]` |
| Measure | prosa longa | `.measure` (70ch) dentro de uma célula |

> A coluna `max-w-6xl` antiga só sobrevive onde houver prosa corrida; caso
> contrário migra para **Wide** ou **Full-bleed**.

## 3. Primitiva: `BlockGrid`

Substitui os grids de cards. Grid modular full-bleed onde os blocos são
separados **só por espaço em branco** (gap generoso), sem nenhuma divisória.

- **Arquivo:** `src/components/lp/block-grid.tsx`
- **Técnica:** `display: grid` com `gap-x`/`gap-y` largos (ex.: `gap-x-16
  gap-y-20`) e **sem** `bg-border`/`gap-px`, **sem** `border`, **sem**
  `rounded-*` por célula. O fundo é uniforme (a superfície da seção). A
  separação é o vazio.
- **API mínima:**

  ```tsx
  <BlockGrid cols={{ base: 2, lg: 12 }} surface="shell">
    <BlockGrid.Cell span={7}>…</BlockGrid.Cell>   {/* conteúdo */}
    <BlockGrid.Cell empty span={5} />              {/* respiro intencional */}
    <BlockGrid.Cell media={…} span={5} />          {/* foto hard-edge */}
  </BlockGrid>
  ```

- **Células:** `type` (manchete/texto), `data` (número mono + label + fonte),
  `media` (imagem `object-cover`, borda dura, sem radius/moldura), `empty`
  (whitespace puro = ritmo).
- **Proibido:** qualquer borda/linha entre blocos, `gap-px bg-border`, hairline,
  `rounded-*`, moldura, card, sombra em repouso.

### Critérios de aceite — BlockGrid

- [ ] **Nenhuma** linha/borda visível entre blocos (separação só por espaço).
- [ ] Suporta célula vazia, de texto, de dado e de mídia.
- [ ] Responsivo: colapsa colunas conforme breakpoint mantendo respiro.
- [ ] Zero `border`/`rounded-*`/`shadow` em repouso; foto hard-edge.

## 4. Primitiva: `FullBleed`

Bloco de mídia na largura total do viewport com conteúdo sobreposto.

- **Arquivo:** `src/components/lp/full-bleed.tsx`
- **Estrutura:** `<section>` 100vw → `<img>` `object-cover` absoluto → **scrim**
  (gradiente shell/carbon a baixa opacidade para garantir contraste) → slot de
  conteúdo (`eyebrow` / `headline` display / `body .measure` / `actions`).
- **Contraste:** texto sobre foto exige scrim que garanta ≥ 4.5:1. Scrim é
  gradiente linear de `--k-color-surface-carbon` (ou shell) com alpha, **não**
  glassmorphism.
- **Altura:** `min-h-screen` no Hero; `min-h-[70svh]` em faixas internas.

### Critérios de aceite — FullBleed

- [ ] Imagem sangra de borda a borda (100vw), `object-cover`, sem letterbox.
- [ ] Scrim garante AA do texto sobreposto (medir com a foto real).
- [ ] Sem `backdrop-blur` decorativo (glass é opt-in explícito, aqui não).
- [ ] `loading`/`decoding` corretos; `alt` significativo ou `alt=""` se decorativa.

## 5. Primitiva: `SceneScrub` (motion em Spec 02)

Generalização do padrão sticky-scrub que hoje vive embutido em
`methodology-block.tsx`. Monta **uma cena por vez** conforme `scrollYProgress`.
Contrato visual aqui; comportamento de motion no `02-motion.md`.

- **Arquivo:** `src/components/lp/scene-scrub.tsx`
- **Estrutura:** wrapper alto (`h-[300vh]` p.ex.) + filho `sticky top-0
  min-h-screen` que troca a cena ativa por índice derivado do progresso.
- **Cada cena:** ocupa o palco inteiro, composição blocada/full-bleed, uma
  ideia/um dado.

### Critérios de aceite — SceneScrub

- [ ] Mostra exatamente uma cena por faixa de progresso.
- [ ] Sob `prefers-reduced-motion`, renderiza as cenas como blocos estáticos
      empilhados (sem prender ao scroll). Ver Spec 02.
- [ ] Interpolação linear (`useTransform`), **sem `useSpring`**.

## 6. Surfaces e ritmo

Sequência tonal ao descer a página (evita monotonia, sem borda de card):

```
Hero(foto/carbon scrim) → shell → fog → carbon → shell → fog → carbon → shell(CTA foto)
```

- Alternar superfície a cada seção ou par de seções.
- `carbon` libera `k-bright` como primary (só em superfície escura, ≤3% de área).
- Transição entre seções: **só a troca de superfície** (a cor muda), sem linha
  divisória nem sombra. A própria mudança tonal já separa.

## 7. Forma e espaço

- **Radius:** mantém 4 a 8px **apenas** em controles (botões, badges, switch).
  Blocos de conteúdo e fotos são **afiados** (sem radius) e **sem borda**.
- **Spacing:** o espaço em branco é a ferramenta principal de separação. Variar
  ritmo vertical (não usar o mesmo `py` em tudo); gutters largos entre blocos.
- **Tap target** ≥ 44px no mobile (`size="lg"`).

## 8. Anti-padrões (match-and-refuse)

- ❌ **Qualquer borda/linha divisória entre blocos** (`gap-px bg-border`,
  hairline, `border-y` entre seções). → separar por espaço e superfície.
- ❌ Card arredondado/com borda como recipiente. → bloco no grid, hard-edge.
- ❌ Tudo em `max-w-6xl` centralizado. → Wide/Full-bleed.
- ❌ Stripe colorida lateral (`border-left/right > 1px`). → nada.
- ❌ Gradiente em headline (`background-clip:text`). → cor sólida + peso.
- ❌ Glassmorphism por padrão / sombra em repouso. → scrim sólido; profundidade tonal.

## 9. Checklist de regressão (preservar)

- [ ] `src/style.css` tokens, escalas, easings e focus ring intactos (só adição
      documentada de `--gutter`/`--block-max`).
- [ ] `lib/motion.ts` helpers intactos.
- [ ] Loader, Cursor, Footer, Sidebar e rota `/mapa` sem regressão.
- [ ] Focus ring 3px `--ring` @40% preservado em todos os interativos.
