<script lang="ts">
  import Showcase from "./lib/Showcase.svelte";
  import { Messaging } from "@footron/messaging";
  import { createNoise2D } from "simplex-noise";
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import { tick } from "svelte";
  import { v4 as uuidv4 } from "uuid";
  import { current_component } from "svelte/internal";

  const serverUrl = "http://monster.cs.byu.edu:32553";
  // const serverUrl = "http://localhost:32553";

  let generationId: string | null = null;

  onMount(() => {
    timer = setTimeout(start_autopilot, 100);

    const messaging = new Messaging();
    messaging.mount();
    messaging.addMessageListener(async (controlsPrompt) => {
      if (typeof controlsPrompt !== "string") {
        throw new Error("Message body must be a string");
      }

      clearTimeout(timer);
      retypeNextPrompt(controlsPrompt);
      let image_blobs = await generateImages(controlsPrompt);
      image_blobs.forEach(async (blob) => {
        const base64Image = await blobToBase64(blob);
        messaging.sendMessage(base64Image);
      });
    });
    messaging.addConnectionListener((connection) => {
      clearTimeout(timer);
      prompt = "";
      displayText("");
      autopilot = false;
      generationId = null;
      show = false;
      image_urls = [];
      connection.addCloseListener(() => {
        autopilot = true;
        show = false;
        image_urls = [];
        start_autopilot();
      });
    });
  });

  function blobToBase64(blob: Blob) {
    return new Promise((resolve, _) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  }

  const noise2D = createNoise2D();
  const noise = (
    (t) => () =>
      noise2D((t += 0.02), 0)
  )(0);

  const typeWait = () => 100 + noise() * 25;
  const backspaceWait = 40;
  const displayImagesWait = 10_000;
  const contentTransitionDuration = 500;

  let prompt = "";
  let image_urls: string[] = [];
  let autopilot = true;
  let show = false;

  let promptElement: HTMLHeadingElement;
  let timer: ReturnType<typeof setTimeout>;

  $: {
    if (show && image_urls.length === 4 && autopilot) {
      timer = setTimeout(() => {
        start_autopilot();
      }, displayImagesWait);
    }
  }

  async function start_autopilot() {
    let nextPrompt = await get_random_prompt();
    if (prompt === nextPrompt) {
      nextPrompt = await get_random_prompt();
    }
    retypeNextPrompt(nextPrompt);
    generateImages(nextPrompt);
  }

  function retypeNextPrompt(nextPrompt: string) {
    if (prompt === nextPrompt) {
      return;
    }
    show = false;
    image_urls = [];
    let diffAt = [...prompt].findIndex((char, i) => char !== nextPrompt[i]);
    diffAt = diffAt === -1 ? prompt.length : diffAt;
    timer = setTimeout(() => {
      backspace(prompt, diffAt, async () => {
        prompt = nextPrompt;
        type(nextPrompt, diffAt, () => {
          show = true;
        });
      });
    }, contentTransitionDuration);
  }

  async function generateImages(prompt: string) {
    const image_blobs = [];
    const currentGenerationId = uuidv4();
    generationId = currentGenerationId;
    for (let i = 0; i < 4; i++) {
      const image = await generate(`${serverUrl}/generate/${prompt}`);
      image_blobs.push(image);
      const imageUrl = URL.createObjectURL(image);
      if (currentGenerationId !== generationId) {
        show = false;
        image_urls = [];
        return [];
      }
      image_urls = [...image_urls, imageUrl];
    }
    return image_blobs;
  }

  async function generate(url: string) {
    const generateResponse = await fetch(url);
    const image = await generateResponse.blob();
    return image;
  }

  async function get_random_prompt() {
    const response = await fetch(`${serverUrl}/random-prompt`);
    return await response.text();
  }

  function type(text: string, from: number, onComplete: () => void) {
    clearTimeout(timer);
    typeKey(text, from, onComplete);
  }

  function typeKey(text: string, index = 0, onComplete: () => void) {
    if (index > text.length) {
      return onComplete();
    }
    displayText(text.slice(0, index));
    timer = setTimeout(() => typeKey(text, index + 1, onComplete), typeWait());
  }

  function backspace(text: string, to: number, onComplete: () => void) {
    clearTimeout(timer);
    backspaceKey(text, to, text.length, onComplete);
  }

  function backspaceKey(
    text: string,
    to: number,
    from: number,
    onComplete: () => void
  ) {
    if (from < to) {
      return onComplete();
    }
    displayText(text.slice(0, from));
    timer = setTimeout(
      () => backspaceKey(text, to, from - 1, onComplete),
      backspaceWait
    );
  }

  function displayText(text: string) {
    // Add zero-width non-breaking space at the end to show typing spaces
    promptElement.innerHTML =
      text + "&#xfeff;" + '<span class="caret" aria-hidden="true" />';
  }

  function map(val: number, x1: number, x2: number, y1: number, y2: number) {
    return y1 + ((val - x1) * (y2 - y1)) / (x2 - x1);
  }
</script>

<Showcase />
<section class="layer front" class:darker={show}>
  <article class="images">
    {#if show}
      {#each Array(4) as _, i}
        <div
          class="img-container"
          in:fade={{ duration: contentTransitionDuration }}
          out:fade={{ duration: contentTransitionDuration }}
        >
          {#if i < image_urls.length}
            <img
              src={image_urls[i]}
              alt="AI generated {prompt}"
              transition:fade={{
                duration: contentTransitionDuration,
              }}
            />
          {:else}
            <div class="shimmer" />
          {/if}
        </div>
      {/each}
    {/if}
  </article>
  <h1
    bind:this={promptElement}
    style:--len-step={map(prompt.length, 0, 500, 7, 1)}
  >
    <span class="caret" aria-hidden="true" />
  </h1>
  <p class="tagline">
    These images are being generated in real-time from the prompt above. Try
    making your own!
  </p>
</section>

<style>
  @font-face {
    font-family: "InterV";
    src: url("./assets/Inter-V.var.woff2") format("woff2 supports variations"),
      url("./assets/Inter-V.var.woff2") format("woff2-variations");
    font-weight: 100 1000;
  }

  :global(:root) {
    --shimmer-spread: 25%;
  }

  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    font-family: sans-serif;
    font-family: "InterV", sans-serif;
    position: relative;
    background: black;
    color: white;
  }

  .layer {
    position: absolute;
    width: 100%;
    height: 100vh;
  }

  @property --top-color {
    syntax: "<color>";
    initial-value: rgba(0, 0, 0, 0.3);
    inherits: false;
  }

  .front {
    z-index: 1;
    background: linear-gradient(
      to bottom,
      var(--top-color) 0%,
      rgba(0, 0, 0, 0.85) 100%
    );
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: --top-color calc(var(--duration) * 0.001s) ease-in-out;
  }

  .darker {
    --top-color: rgba(0, 0, 0, 0.85);
  }

  .images {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 3rem;
    position: relative;
    overflow: hidden;
  }

  h1 {
    font-size: calc(var(--len-step) * 1rem);
    word-break: break-word;
    font-weight: bold;
    margin: 0;
    max-width: 80%;
    text-align: center;
  }

  .tagline {
    font-size: 3rem;
    font-weight: 500;
    color: #ccc;
    margin: 2rem 0 4rem;
  }

  :global(.caret) {
    border-right: 0.05em solid;
    animation: caret 1s steps(1) infinite;
  }

  @keyframes caret {
    50% {
      border-color: transparent;
    }
  }

  .img-container {
    width: 610px;
    height: 610px;
    background-color: #444;
  }

  .shimmer,
  img {
    width: 100%;
    height: 100%;
  }

  .shimmer {
    clip-path: inset(0);
  }

  .shimmer::before {
    content: "";
    position: absolute;
    z-index: -1;
    inset: 0;
    transform: translateX(calc(-60% - (var(--shimmer-spread) / 2)));
    animation: shimmer 1.5s infinite;
    animation-delay: 500ms;
    background: linear-gradient(
      -80deg,
      rgba(0, 0, 0, 0) calc(50% - (var(--shimmer-spread) / 2)),
      #494949 50%,
      rgba(0, 0, 0, 0) calc(50% + (var(--shimmer-spread) / 2))
    );
  }

  @keyframes shimmer {
    100% {
      transform: translateX(calc(60% + (var(--shimmer-spread) / 2)));
    }
  }
</style>
