/**
 * Reference-only lifecycle token. Guards capture internally and cannot be
 * future-armed. Numeric tokens are captured snapshots, never synthesized.
 * Overflow fails closed instead of wrapping. Async continuations must re-check.
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
  public capture(): number { return this.value; }
  public isCurrent(epoch: number): boolean { return Number.isSafeInteger(epoch) && epoch === this.value; }

  public advance(): number {
    if (this.value >= Number.MAX_SAFE_INTEGER) {
      throw new Error('LifecycleEpoch exhausted; refusing to wrap and accept stale callbacks');
    }
    this.value += 1;
    return this.value;
  }

  /**
   * Captures the current epoch internally. Suppression is checked only when
   * the wrapper is entered; an async continuation must re-check ownership.
   */
  public guard<T extends readonly unknown[]>(
    callback: (...args: T) => void,
  ): (...args: T) => boolean {
    if (typeof callback !== 'function') {
      throw new Error('LifecycleEpoch guard callback must be a function');
    }
    const epoch = this.capture();
    return (...args: T): boolean => {
      if (!this.isCurrent(epoch)) return false;
      callback(...args);
      return true;
    };
  }
}
