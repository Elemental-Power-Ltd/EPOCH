import * as React from "react";

type PresentationMode = {
    enabled: boolean;
    setEnabled: (v: boolean) => void;
    toggle: () => void;
};

const PresentationModeContext = React.createContext<PresentationMode | null>(null);

export function PresentationModeProvider({children, defaultEnabled = false,}:
                                         {children: React.ReactNode; defaultEnabled?: boolean;}) {
    const [enabled, setEnabled] = React.useState(defaultEnabled);
    const toggle = React.useCallback(() => setEnabled((v) => !v), []);

    const value = React.useMemo(() => ({enabled, setEnabled, toggle}), [enabled, toggle]);

    return (
        <PresentationModeContext.Provider value={value}>
            {children}
        </PresentationModeContext.Provider>
    );
}

export function usePresentationMode(): PresentationMode {
    const ctx = React.useContext(PresentationModeContext);
    // default to presentationMode: false
    return (
        ctx ?? {
            enabled: false,
            setEnabled: () => {
            },
            toggle: () => {
            },
        }
    );
}
