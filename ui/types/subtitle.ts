interface Word {
    text: string;
    start: number;
    end: number;
}

export interface Subtitle {
    start: number;
    end: number;
    alignX: string;
    alignY: string;
    x?: number;
    y?: number;
    bottom?: number;
    font_size: number;
    words: Word[];
}
