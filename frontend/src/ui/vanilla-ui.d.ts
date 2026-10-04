// The published Vanilla UI package does not include TypeScript declarations.
// Keep these small declarations limited to the components this app actually uses.
declare module '@vanilla-primitives/styled' {
    export function defineVanillaUI(config: { components: Record<string, CustomElementConstructor> }): void;
}
declare module '@vanilla-primitives/styled/shadcn-default-css/button.js' {
    export class Button extends HTMLElement {}
}
declare module '@vanilla-primitives/styled/shadcn-default/card.js' {
    export class Card extends HTMLElement {}
    export class CardHeader extends HTMLElement {}
    export class CardTitle extends HTMLElement {}
    export class CardDescription extends HTMLElement {}
    export class CardContent extends HTMLElement {}
    export class CardFooter extends HTMLElement {}
}
declare module '@vanilla-primitives/styled/shadcn-default/label.js' {
    export class Label extends HTMLElement {}
}
declare module '@vanilla-primitives/styled/shadcn-default/switch.js' {
    export class Switch extends HTMLElement {
        switchBtn: HTMLButtonElement;
        toggle(): void;
    }
}
