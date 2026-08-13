/**
 * Reference-only monotonic lifecycle identity. Callback scheduling and stale
 * suppression belong to the runtime lifecycle owner, not this value object.
 */
export class LifecycleEpoch {
  private value: number;

  public constructor(initialValue = 0) {
    if (!Number.isSafeInteger(initialValue) || initialValue < 0) {
      throw new Error('LifecycleEpoch initial value must be a non-negative safe integer');
    }
    this.value = initialValue === 0 ? 0 : initialValue;
  }

  public current(): number { return this.value; }
  public isCurrent(epoch: number): boolean {
    return Number.isSafeInteger(epoch) && epoch >= 0 && epoch === this.value;
  }

  public advance(): number {
    if (this.value >= Number.MAX_SAFE_INTEGER) {
      throw new Error('LifecycleEpoch exhausted; refusing to wrap and reactivate stale callbacks');
    }
    this.value += 1;
    return this.value;
  }
}
