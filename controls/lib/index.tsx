/** @jsxImportSource @emotion/react */
import { useState, useCallback } from "react";
import { useMessaging } from "@footron/controls-client";
import options from "./options.json";
import "./styles.css";

const ControlsComponent = (): JSX.Element => {
  const [images, setImages] = useState<string[]>([]);
  const onMessage = useCallback((image_str: string) => {
    setImages((prevImages) => [...prevImages, image_str]);
  }, []);

  const { sendMessage } = useMessaging(onMessage);

  const [selected, setSelected] = useState<[number, number][]>([]);
  const [currentGroupIndex, setCurrentGroupIndex] = useState<number>(0);
  const currentOptions = options[currentGroupIndex];
  const selectedOptions = selected.map(
    ([groupIndex, optionIndex]) => options[groupIndex][optionIndex]
  );
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const text = selectedOptions.join(" ");

  const isSelectedEmpty = selected.length === 0;
  const isFirstGroup = currentGroupIndex === 0;
  const isSkipAble = currentGroupIndex < options.length - 1;

  function addOption(groupIndex: number, optionIndex: number) {
    setSelected((prev) => [...prev, [groupIndex, optionIndex]]);
    setCurrentGroupIndex((prev) => prev + 1);
  }

  function clear() {
    setSelected([]);
    setCurrentGroupIndex(0);
  }

  function startOver() {
    clear();
    setImages([]);
    setIsGenerating(false);
  }

  function back() {
    if (!isSelectedEmpty) {
      const lastSelectedGroupIndex = selected.at(-1)![0];
      if (lastSelectedGroupIndex === currentGroupIndex - 1) {
        setSelected(selected.slice(0, -1));
      }
    }
    setCurrentGroupIndex((prev) => prev - 1);
  }

  function skip() {
    setCurrentGroupIndex((prev) => prev + 1);
  }

  function generate() {
    setIsGenerating(true);
    sendMessage(text);
  }

  return (
    <div className="controls">
      <div className="button-section">
        <div>
          <button onClick={clear} disabled={isSelectedEmpty || isGenerating}>
            Clear
          </button>
          <button onClick={back} disabled={isFirstGroup || isGenerating}>
            Back
          </button>
          <button onClick={skip} disabled={!isSkipAble || isGenerating}>
            Skip
          </button>
        </div>
        <button className="generate" onClick={generate} disabled={isSelectedEmpty || isGenerating}>
          Generate
        </button>
      </div>
      <h2 title={text}>Selected</h2>
      <section className="selected">
        <div className="flex">
          {selected.map(([groupIndex, optionIndex]) => (
            <div
              key={`selected-${groupIndex}-${optionIndex}`}
              className="option"
            >
              {options[groupIndex][optionIndex]}
            </div>
          ))}
        </div>
      </section>
      {isGenerating ? (
        <>
          <h2>{images.length === 0 ? "Generating..." : "Generation"}</h2>
          <div className="button-row">
            <button onClick={startOver}>Start Over</button>
          </div>
          {images.length > 0 && <p>Click on an image to download it.</p>}
          <div className="images">
            {images.map((image, i) => (
              <a key={i} href={image} download={`${text} (${i}).webp`}>
                <img src={image} />
              </a>
            ))}
          </div>
        </>
      ) : (
        <>
          <h2>Options</h2>
          <section className="options">
            <div className="flex">
              {currentGroupIndex < options.length &&
                currentOptions.map((option, i) => (
                  <div
                    key={`option-${currentGroupIndex}-${i}`}
                    onClick={() => addOption(currentGroupIndex, i)}
                    className="option"
                  >
                    {option}
                  </div>
                ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default ControlsComponent;
