import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {GenericVideo} from './GenericVideo';
import type {MEditVideoProps} from './types';

const defaultProps: MEditVideoProps = {
  src: 'm-edit-assets/source.mp4',
  durationInSeconds: 10,
  width: 1920,
  height: 1080,
  fps: 30,
  captions: [],
  captionStyle: {enabled: true, position: 'bottom'},
  fit: 'cover',
  backgroundColor: '#000000',
};

const calculateMetadata: CalculateMetadataFunction<MEditVideoProps> = ({props}) => {
  const fps = props.fps ?? 30;
  const width = props.width ?? 1920;
  const height = props.height ?? 1080;
  return {
    durationInFrames: Math.max(1, Math.ceil(props.durationInSeconds * fps)),
    fps,
    width,
    height,
  };
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="MEditVideo"
    component={GenericVideo}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={defaultProps}
    calculateMetadata={calculateMetadata}
  />
);
