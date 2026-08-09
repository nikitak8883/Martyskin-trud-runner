/** Reference-only lifecycle token. Overflow fails closed instead of wrapping. */
export class LifecycleEpoch {
  private value: number;

  public constructor(initialValue = 0) {
    if (!Number.isSafeInteger(initialValue) || initialValue < 0) {
      throw new Error(`LifecycleEpoch initial value must be a non-negative safe integer, got ${initialValue}`);
    }
    this.value = initialValue;
  }

  public current(): number { return this.value; }
  public capture(): number { return this.value; }
  public isCurrent(epoch: number): boolean { return Number.isSafeInteger(epoch) && epoch === this.value; }

  public advance(): number {
    if (this.value >= Number.MAX_SAFE_INTEGER) {
      throw new Error('LifecycleEpoch exhausted; refusing to wrap and accept stale callbacks');
    }
    this.value += 1;
    return this.value;
  }

  public guard<T extends readonly unknown[]>(
    epoch: number,
    callback: (...args: T) => void,
  ): (...args: T) => boolean {
    return (...args: T): boolean => {
      if (!this.isCurrent(epoch)) return false;
      callback(...args);
      return true;
    };
  }
}
