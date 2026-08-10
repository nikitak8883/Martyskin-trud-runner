/**
 * Pure lifecycle token used to suppress deferred work after an owner advances.
 *
 * Guards capture the current epoch internally, so callers cannot arm a guard
 * with a future value that becomes active later. Numeric tokens returned by
 * capture() are meaningful only as captured snapshots and must not be
 * synthesized. This is a suppression primitive, not callback cancellation or
 * a scheduling owner. The check happens only when the wrapper is entered;
 * async continuations need their own ownership check.
 */
export class LifecycleEpoch {
  private value: number;

  public constructor(initialValue = 0) {
    if (!Number.isSafeInteger(initialValue) || initialValue < 0) {
      throw new Error('LifecycleEpoch initial value must be a non-negative safe integer');
    }
    this.value = initialValue === 0 ? 0 : initialValue;
  }

  public current(): number {
    return this.value;
  }

  public capture(): number {
    return this.value;
  }

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

  public guard<TArgs extends readonly unknown[]>(
    callback: (...args: TArgs) => void,
  ): (...args: TArgs) => boolean {
    if (typeof callback !== 'function') {
      throw new Error('LifecycleEpoch guard callback must be a function');
    }

    const capturedEpoch = this.capture();
    return (...args: TArgs): boolean => {
      if (!this.isCurrent(capturedEpoch)) {
        return false;
      }
      callback(...args);
      return true;
    };
  }
}
