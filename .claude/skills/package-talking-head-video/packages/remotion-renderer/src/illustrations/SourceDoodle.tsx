import type {ReactElement} from 'react';
import type {PUBLIC_DOODLE_TYPES} from '../../../core/src/schema';
import {illustrationRegistry} from './index';
import {Frame} from './Frame';
import type {IllustrationProps} from './types';

type DoodleType = (typeof PUBLIC_DOODLE_TYPES)[number];
/** Generic conceptual diagrams. No logos, screenshots or claims of device operation. */
export const SourceDoodle = ({type, ...props}: IllustrationProps & {type: DoodleType}): ReactElement => {
  const shared = {...props, normalized: true};
  const a = Math.max(0, Math.min(1, props.actionProgress ?? 0));
  const route = (from: number, to: number, y: number) => <g data-doodle-action="source-to-result" opacity={props.progress > .7 ? 1 : 0}>
    <circle cx={from + (to - from) * a} cy={y} r="7" fill={props.accent} opacity={a > 0 && a < 1 ? .95 : 0}/>
    <circle cx={to} cy={y} r={8 + 12 * a} stroke={props.accent} strokeWidth="3" fill="none" opacity={a * .8}/>
  </g>;
  if (type === 'phone-mirror') return <Frame {...shared} overlay={route(220, 304, 174)}>
    <rect x="74" y="50" width="118" height="252" rx="19"/>
    <path d="M104 76h57M119 276h29M97 114h70M98 143h50M96 178h71"/>
    <rect x="318" y="91" width="248" height="174" rx="14"/>
    <path d="M347 121h190M346 156h130M347 190h190M446 266v34M386 301h121M220 174h68m-24-20 24 20-24 20"/>
  </Frame>;
  if (type === 'notes') return <Frame {...shared} overlay={route(240, 339, 174)}>
    <path d="M72 77h124v176H72zM96 59h124v176M96 117h69M96 150h69M96 184h44"/>
    <path d="M240 174h75m-23-20 23 20-23 20"/>
    <rect x="358" y="53" width="196" height="254" rx="14"/>
    <path d="M385 88h138M386 125h111M386 162h137M386 199h93M387 249h87"/>
    <path d="m492 247 36-40 14 14-36 40-25 12zM528 207l14 14" stroke={props.accent}/>
  </Frame>;
  if (type === 'agent-output') return <Frame {...shared} overlay={route(281, 395, 181)}>
    <rect x="92" y="100" width="166" height="166" rx="21"/>
    <rect x="129" y="136" width="92" height="93" rx="12"/>
    <path d="M116 76v24M154 76v24M192 76v24M230 76v24M116 266v24M154 266v24M192 266v24M230 266v24M66 128h26M66 168h26M66 208h26M66 246h26"/>
    <path d="M281 181h93m-24-22 24 22-24 22" stroke={props.accent}/>
    <rect x="412" y="63" width="152" height="240" rx="13"/>
    <path d="M438 105h100M438 141h82M438 177h101M438 213h70M438 253h95"/>
  </Frame>;
  const Existing = illustrationRegistry[type];
  return <Existing {...shared}/>;
};
