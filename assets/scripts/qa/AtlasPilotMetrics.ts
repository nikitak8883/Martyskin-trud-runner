export interface AtlasPilotSample {
    sampledAtMs: number;
    draws: number;
    textureMemoryMb: number;
    bufferMemoryMb: number;
    fps: number;
}

export interface AtlasPilotMetricRange {
    min: number;
    median: number;
    max: number;
}

export interface AtlasPilotAggregate {
    sampleCount: number;
    draws: AtlasPilotMetricRange;
    textureMemoryMb: AtlasPilotMetricRange;
    bufferMemoryMb: AtlasPilotMetricRange;
    fps: AtlasPilotMetricRange;
}

function finiteValues(samples: readonly AtlasPilotSample[], key: keyof AtlasPilotSample): number[] {
    return samples
        .map((sample) => sample[key])
        .filter((value) => Number.isFinite(value))
        .sort((a, b) => a - b);
}

function roundMetric(value: number): number {
    return Math.round(value * 1000) / 1000;
}

function metricRange(samples: readonly AtlasPilotSample[], key: keyof AtlasPilotSample): AtlasPilotMetricRange {
    const values = finiteValues(samples, key);
    if (values.length !== samples.length || values.length === 0) {
        throw new Error(`Atlas pilot metric ${String(key)} must contain one finite value per sample.`);
    }
    const middle = Math.floor(values.length / 2);
    const median = values.length % 2 === 0
        ? (values[middle - 1] + values[middle]) / 2
        : values[middle];
    return {
        min: roundMetric(values[0]),
        median: roundMetric(median),
        max: roundMetric(values[values.length - 1]),
    };
}

export function aggregateAtlasPilotSamples(samples: readonly AtlasPilotSample[]): AtlasPilotAggregate {
    if (samples.length === 0) throw new Error('Atlas pilot aggregation requires at least one sample.');
    return {
        sampleCount: samples.length,
        draws: metricRange(samples, 'draws'),
        textureMemoryMb: metricRange(samples, 'textureMemoryMb'),
        bufferMemoryMb: metricRange(samples, 'bufferMemoryMb'),
        fps: metricRange(samples, 'fps'),
    };
}
