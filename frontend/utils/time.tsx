export const timeDiff = (start: string | number, end: string | number) => {
    const startTime = new Date(start);
    const endTime = new Date(end);
    const diff = Math.abs(endTime.getTime() - startTime.getTime());
    return new Date(diff).toISOString().substring(11, 22);
}

export const timeDiffSec = (start: number, end: number) => {
    return timeDiff(start * 1000, end * 1000);
}
