/** Register Vanilla UI once, before querying controls or creating the map. */
import { defineVanillaUI } from '@vanilla-primitives/styled';
import { Button } from '@vanilla-primitives/styled/shadcn-default-css/button.js';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@vanilla-primitives/styled/shadcn-default/card.js';
import { Label } from '@vanilla-primitives/styled/shadcn-default/label.js';
import { Switch } from '@vanilla-primitives/styled/shadcn-default/switch.js';
import '@vanilla-primitives/styled/shadcn-default-css/button.css';

// Version 0.4.3 replaces the custom switch with a button, but dispatches change
// on the detached custom element. Forward it from the visible button instead.
class LayerSwitch extends Switch {
    override toggle() {
        if (this.switchBtn.disabled) return;
        super.toggle();
        this.switchBtn.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

defineVanillaUI({
    components: { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, Label, Switch: LayerSwitch }
});
