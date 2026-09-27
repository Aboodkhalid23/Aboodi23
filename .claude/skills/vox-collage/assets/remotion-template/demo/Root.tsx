import React from 'react';
import {Composition} from 'remotion';
import {VoxCollageDemo} from './VoxCollageDemo';

export const DemoRoot: React.FC = () => (
  <Composition
    id="XingchenVoxCollageDemo"
    component={VoxCollageDemo}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={240}
  />
);
