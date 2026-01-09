# LifeCycle

함수 실행 단위의 lifecycle을 관리한다.

## 사용 예시
- 행위에 대한 metric 생성

## 사용법
class를 상속하여 사용하는 것을 권장한다.
```python
from core.lifecycle import LifeCycle

@LifeCycle.with_lifecycle()
def my_handler():
    lc = LifeCycle.get_lifecycle()
    # lifecycle을 활용한 작업
```
