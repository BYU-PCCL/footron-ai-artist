<script lang="ts">
  import showcaseIds from "../assets/showcase-ids.json";
  import { v4 as uuidv4 } from "uuid";
  import { fade } from "svelte/transition";

  let backgroundImages: [string, string][] = [];

  const numOfBackgroundImages = 70;
  const backgroundImageWait = 150;
  const backgroundImageSize = 215;
  const contentTransitionDuration = 500;

  setInterval(() => {
    const nextImage =
      showcaseIds[Math.floor(Math.random() * showcaseIds.length)];
    backgroundImages = [...backgroundImages, [nextImage, uuidv4()]];
    if (backgroundImages.length > numOfBackgroundImages) {
      backgroundImages = backgroundImages.slice(1);
    }
  }, backgroundImageWait);

</script>

<div class="background layer">
  {#each backgroundImages as [imgId, step], i (step)}
    <div
      class="background-img-wrapper"
      in:fade={{ duration: contentTransitionDuration }}
      style:--size={backgroundImageSize}
      style:--top={Math.random() * (window.innerHeight - backgroundImageSize)}
      style:--left={Math.random() * (window.innerWidth - backgroundImageSize)}
    >
      <img
        style:--opacity={(numOfBackgroundImages -
          backgroundImages.length +
          i) /
          numOfBackgroundImages}
        class="repo-img"
        src="showcase-imgs/{imgId}.jpeg"
        alt="generated..."
      />
    </div>
  {/each}
</div>

<style>
  .background-img-wrapper {
    background-color: black;
    position: absolute;
    top: calc(var(--top) * 1px);
    left: calc(var(--left) * 1px);
    width: calc(var(--size) * 1px);
    height: calc(var(--size) * 1px);
  }

  .repo-img {
    width: 100%;
    height: 100%;
    opacity: var(--opacity);
  }

  .layer {
    position: absolute !important;
    width: 100%;
    height: 100vh;
  }

  .background {
    position: relative;
    z-index: -1;
    background: black;
    overflow: hidden;
    width: 100%;
    height: 100vh;
  }
</style>