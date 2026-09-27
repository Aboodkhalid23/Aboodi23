import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {
  DrawnArrow,
  KineticType,
  PaperActor,
  PaperSubstrate,
  TornPaper,
  VOX_PALETTE,
  VOX_SHADOW,
  restrainedPush,
} from '../../vox-collage';

const Mountain: React.FC<{color: string; points: string}> = ({color, points}) => (
  <svg viewBox="0 0 1000 600" style={{width: '100%', height: '100%', filter: VOX_SHADOW}}>
    <polygon points={points} fill={color} />
  </svg>
);

const SnowballScene: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = restrainedPush(frame, 120, 0.04);
  return (
    <PaperSubstrate color={VOX_PALETTE.plum}>
      <AbsoluteFill style={{transform: `scale(${scale})`}}>
        <PaperActor x={1080} y={650} width={1450} height={640} rotate={-7} fromX={-220} fromY={260} enterFrame={0} duration={22}>
          <TornPaper seed={4} color={VOX_PALETTE.paper} style={{width: '100%', height: '100%'}}>
            <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(135deg, transparent 0 50%, rgba(23,111,103,.15) 50% 100%)'}} />
          </TornPaper>
        </PaperActor>

        <PaperActor x={1290} y={775} width={980} height={360} rotate={-5} fromX={320} fromY={180} enterFrame={9} duration={20}>
          <Mountain color="#2d3431" points="0,590 120,390 230,470 410,235 535,390 700,160 1000,580" />
        </PaperActor>

        <PaperActor x={1480} y={760} width={270} height={270} z={8} fromX={-920} fromY={-570} fromScale={0.16} fromRotate={-260} enterFrame={18} duration={64}>
          <div
            style={{
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              background: VOX_PALETTE.cream,
              border: `12px solid ${VOX_PALETTE.ink}`,
              filter: VOX_SHADOW,
              backgroundImage: 'radial-gradient(circle, rgba(24,43,39,.35) 0 1.2px, transparent 1.4px)',
              backgroundSize: '9px 9px',
            }}
          />
        </PaperActor>

        <PaperActor x={515} y={260} width={650} height={245} z={12} fromX={-500} fromRotate={-8} enterFrame={5} duration={20}>
          <TornPaper seed={8} color={VOX_PALETTE.mustard} style={{padding: '34px 48px'}}>
            <KineticType text="小问题" fontSize={104} enterFrame={9} />
            <KineticType text="会滚成大后果" fontSize={76} enterFrame={17} color={VOX_PALETTE.vermilion} />
          </TornPaper>
        </PaperActor>

        <PaperActor x={1050} y={360} width={610} height={300} z={15} enterFrame={48} duration={18}>
          <DrawnArrow
            path="M30 42 C170 0 250 80 320 140 C390 200 450 210 525 260 M525 260 L475 252 M525 260 L505 214"
            viewBox="0 0 560 300"
            color={VOX_PALETTE.vermilion}
            strokeWidth={16}
            enterFrame={48}
          />
        </PaperActor>

        <PaperActor x={1330} y={410} z={16} fromScale={1.28} fromRotate={8} enterFrame={70} duration={13}>
          <TornPaper seed={19} color={VOX_PALETTE.vermilion} style={{padding: '16px 26px'}}>
            <div style={{fontSize: 42, fontWeight: 900, color: VOX_PALETTE.paper}}>越滚越大</div>
          </TornPaper>
        </PaperActor>
      </AbsoluteFill>
    </PaperSubstrate>
  );
};

const Dot: React.FC<{index: number}> = ({index}) => {
  const col = index % 6;
  const row = Math.floor(index / 6);
  return (
    <PaperActor
      x={1110 + col * 105 + (row % 2) * 28}
      y={290 + row * 112}
      width={68}
      height={68}
      fromScale={1.34}
      fromRotate={(index % 5) * 4 - 8}
      enterFrame={22 + index * 2}
      duration={12}
      z={5 + row}
    >
      <div
        style={{
          width: '100%',
          height: '100%',
          borderRadius: index % 3 === 0 ? '14% 52% 38% 48%' : '50%',
          background: index % 7 === 0 ? VOX_PALETTE.vermilion : VOX_PALETTE.paper,
          border: `5px solid ${VOX_PALETTE.ink}`,
          filter: VOX_SHADOW,
        }}
      />
    </PaperActor>
  );
};

const SpreadScene: React.FC = () => {
  const frame = useCurrentFrame();
  const redField = interpolate(frame, [0, 86, 119], [0, 0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <PaperSubstrate color={VOX_PALETTE.mustard}>
      <PaperActor x={420} y={520} width={420} height={620} rotate={-2} fromX={-420} enterFrame={0} duration={18}>
        <TornPaper seed={33} color={VOX_PALETTE.paper} style={{height: '100%', padding: '58px 46px'}}>
          <div style={{fontSize: 36, fontWeight: 800, color: VOX_PALETTE.softInk}}>起点</div>
          <KineticType text="1" fontSize={260} enterFrame={6} color={VOX_PALETTE.vermilion} style={{marginTop: 30}} />
          <div style={{fontSize: 44, lineHeight: 1.2, fontWeight: 900, marginTop: 26}}>一个动作</div>
        </TornPaper>
      </PaperActor>

      <PaperActor x={810} y={520} width={360} height={250} z={15} enterFrame={14} duration={18}>
        <DrawnArrow
          path="M20 125 C90 40 170 35 260 110 M260 110 L220 72 M260 110 L212 132"
          viewBox="0 0 300 180"
          color={VOX_PALETTE.vermilion}
          strokeWidth={15}
          enterFrame={15}
        />
      </PaperActor>

      {Array.from({length: 24}, (_, index) => <Dot index={index} key={index} />)}

      <PaperActor x={1365} y={805} width={760} height={180} z={30} fromY={160} enterFrame={62} duration={18}>
        <TornPaper seed={51} color={VOX_PALETTE.ink} style={{padding: '30px 42px'}}>
          <KineticType text="不是加法，是扩散" fontSize={74} enterFrame={66} color={VOX_PALETTE.paper} align="center" />
        </TornPaper>
      </PaperActor>

      <AbsoluteFill
        style={{
          background: VOX_PALETTE.vermilion,
          transform: `translateX(${(1 - redField) * 1920}px) rotate(-3deg) scale(1.1)`,
          transformOrigin: 'right center',
          zIndex: 80,
        }}
      />
    </PaperSubstrate>
  );
};

export const VoxCollageDemo: React.FC = () => (
  <AbsoluteFill>
    <Sequence from={0} durationInFrames={120} premountFor={30}>
      <SnowballScene />
    </Sequence>
    <Sequence from={120} durationInFrames={120} premountFor={30}>
      <SpreadScene />
    </Sequence>
  </AbsoluteFill>
);
