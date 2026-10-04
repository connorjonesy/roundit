/** Vanilla UI switches become native buttons with aria-checked state. */
export function getLayerControls() {
    const fieldset = document.querySelector<HTMLFieldSetElement>('#layer-controls')!;
    const heat = document.querySelector<HTMLButtonElement>('#show-heatmap')!;
    const points = document.querySelector<HTMLButtonElement>('#show-points')!;
    return {
        state: () => ({ heat: heat.getAttribute('aria-checked') === 'true', points: points.getAttribute('aria-checked') === 'true' }),
        setDisabled(disabled: boolean) {
            fieldset.disabled = disabled;
            for (const control of [heat, points]) {
                control.disabled = disabled;
                control.setAttribute('aria-disabled', String(disabled));
            }
        },
        onChange(callback: () => void) {
            heat.addEventListener('change', callback);
            points.addEventListener('change', callback);
        }
    };
}
