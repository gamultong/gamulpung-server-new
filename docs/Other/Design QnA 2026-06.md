# 설계 문답 (2026-06)

구조 감사 후 "이유를 알 수 없던" 컨벤션·패턴·아키텍처에 대해 질문하고 받은 원문 답변 기록. 답변의 성격에 따라 ADR·RFC·코드로 반영했으며, 반영 위치를 각 항목에 표시한다.

## 아키텍처

**Q1. domain logic이 Handler가 아닌 Receiver 소속인 이유는?**
> 로직은 항상 단순해야함. 프로그램의 복잡성은 State에서 옴, 이는 설계를 Easy하게 하지만, Simple하지 못하게 함. 단지 Domain Logic에 State를 제거함으로 추상화된 Simple과, Easy를 제공한거임.

반영: [[ADR-003] HR Architecture 채택 배경](/docs/ADR/%5BADR-003%5D%20HR%20Architecture%20채택%20배경.md)

**Q2. EventBroker를 자체 구현한 이유는?**
> 별 이유 없음. 그냥 처음에 Kafka나 RabbitMQ를 쓰는 것은 과한 설계라 생각함. 또한 인메모리 큐를 기본 베이스로 해야 Kafka나 RabbitMQ 마이그레이션 확장성이 좋다 판단함.

반영: [[ADR-004] 인메모리 우선 인프라 채택](/docs/ADR/%5BADR-004%5D%20인메모리%20우선%20인프라%20채택.md)

**Q3. 단일 프로세스 전제(인메모리 dict + SQLite)는 의도인가?**
> 보면 dict 같은거 Storage/Space Interface가 있음, 이것도 마찬가지로 외부 확장을 고려한거임. 그저 필요성을 못 느껴서 안 했고, Board 저장의 경우는 확장 사례가 있음.

반영: [[ADR-004] 인메모리 우선 인프라 채택](/docs/ADR/%5BADR-004%5D%20인메모리%20우선%20인프라%20채택.md)

**Q4. LifeCycle은 왜 있나? (표준 트레이싱 대신 자체 추상화, snapshot의 최종 용도)**
> 함수에 대한 처리. Event는 Obj의 상태 변경이고, Handler에서 발생된 Event는 사실 자동으로 캡쳐되고 Publish 되어야 함. 근데 지금까지는 그게 Function의 inline에서 된 거고 이는 엄청난 Boiler Plate이자 코드적 복잡성임. 그래서 이를 해결할 Function의 platform(Framework?)이 필요했고, 이게 LifeCycle임. 사실 Observability는 그 Platform 위에 올라간 기능인 거임. 또한 함수의 Inline에서 Function Manage에 관여할 수 있어야 했음. 왜냐면 Return과 Parameter 같은 함수 내외부 통로는 시점도 고정적일 뿐만 아니라 함수의 Interface도 혼란시키는 좋지 않은 패턴이었음. 또한 외부 패턴 고착화는 하나의 다른 Boiler Plate고, 그래서 인라인 접근이 되게 만든 것.

반영: [[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md) 목적 수정 (플랫폼이 본질, Observability는 그 위의 기능)

**Q5. Emitter는 왜 있나?**
> 위 4번이랑 동기는 비슷하고, LifeCycle Platform에 올라간 또 다른 기능. old와 new를 캡쳐해서 Event를 계산하는 거임. Event 발행은 Handler지만(State 변경이 일어남), Event 선언은 Data거든(Struct에 대한 정의, 변경의 의미 정의 같은 느낌). 그래서 자동이어야 했고.

반영: [[RFC-009] Emitter](/docs/RFC/%5BRFC-009%5D%20Emitter.md) 목적 보강

## 패턴·메커니즘

**Q6. Handler가 전부 classmethod 정적 클래스인 이유는?**
> Singleton에 대한 내 취향. 난 Singleton을 쓸 때 class를 애용함. 이건 애초에 언어적으로 하나의 개체가 보장되고, 사용 코드 디자인도 깔끔해서(cls().mtd X | cls.mtd O). Handler는 Obj를 관리하는 Manage 개체이고, 관리에 필요한 State(애초에 관리되는 Obj 자체도 Handler의 State)가 있어서 Obj인 건 당연하고, 현재는 소스가 한 곳에서만 관리되는 게 맞고, 소스 단일 원천을 지키는 게 맞다 생각해서 Singleton 사용함.

반영: 기록 보존 (컨벤션 규칙 자체는 [HR 구현 가이드](/docs/Other/Convention%20guide/HR.md))

**Q7. DataObj의 자동 dataclass 메커니즘의 의도는?**
> 데코 붙이는 게 너무나도 Boiler Plate였음. 그냥 @deco 붙이면 너무 안 예쁨, 그리고 어차피 DataObj에 대한 관리가 필요해서 상속은 필수였음. 그냥 그 Boiler Plate들을 한 곳에 몰아서 줄인 거고, 그 중 이미 있는 Pattern을 사용한 것(Django ORM이나 SQLAlchemy).

반영: 기록 보존

**Q8. 이벤트 scope 누적 메커니즘의 의도된 용도는?**
> Event 관리 편하게 하려고 계층형 관리한 거임. 나중 되면 log 조회에 필터 걸 수도 있고, 멘탈 모델에도 handler를 기반으로 Event 찾는 게 쉽기도 하고, 여러모로 편함.

반영: [event](/docs/Glossary/dev/event.md) 정의 보강

**Q9. 트랜잭션 경계 부재(함수별 commit)는 의도인가?**
> 애초에 실패하면 그 단에서 끝나야지. handler, receiver가 원자성 단위기도 했고, 도메인 특성상 그냥 데이터 정합성이 그렇게 중요하지 않음. 그래서 Event 실패에 대해 무감함.

반영: [[ADR-005] 데이터 정합성 수준 채택](/docs/ADR/%5BADR-005%5D%20데이터%20정합성%20수준%20채택.md)

**Q10. dodoenv를 커스텀 패키지로 뺀 이유는?**
> 그냥, 코드 디자인 ㅈㄴ 예쁘잖음.

반영: 기록 보존

## 프로토콜·게임 규칙

**Q11. 닫힌 타일의 mine 비트가 와이어로 전송되는 것은 의도인가?**
> 높은 확률로 실수, client한테 가는 것 중 close는 다 hide되어야 함.

반영: 코드 수정 — 클라이언트 전송 경로에 마스킹 적용, [[RFC-006] Tile 마스킹](/docs/RFC/%5BRFC-006%5D%20Tile%20마스킹.md)에 규칙 추가

**Q12. 점수 규칙(이동 +1, 오픈 +100, 깃발 +10)의 출처는?**
> 이건 그냥 임시로 정한 것. 게임 진행에 높은 중요도 인터랙션별 차등 지급한 거고, 이동 또한 게임 진행으로 보나 이게 게임 진행에 유의미하진 않다 본 거임.

반영: 기록 보존 (임시 값 — 공식화 보류)

**Q13. color 중복을 허용으로 바꾼 이유는?**
> 애초에 color는 중복이 됐는데? 원래는 "불특정 다수의 인터랙션"이 프로젝트 모토였어서 color 없애려 했는데, color 색 가짓수를 줄이고 중복을 허용해서 완전 특정이 아닌 유추적 특정성으로 허용한 거임. 이로써 커서에 대한 사용자 가시성을 챙긴 것. 대충 "아 방금 개트롤한 저 노랑이" 정도의 특정성이지.

반영: [[ADR-006] Color 유추적 특정성 채택](/docs/ADR/%5BADR-006%5D%20Color%20유추적%20특정성%20채택.md)

**Q14. 부활·점수·무한맵 룰의 게임 디자인 의도는?**
> 무한 지뢰찾기에는 승리 규칙이 없음. 그래서 점수 만들고, 맵 넓히고, 죽으면 부활시킨 거. 애초에 멀티니까, 그에 맞춰 룰을 좀 바꾼 거지.

반영: 기록 보존

## 추가 문답 (평가에 대한 반론)

**Q2+Q3 보충 — 브로커 의미론(동기·순서)이 인메모리에 묶이면 마이그레이션이 깨지지 않나?**
> 그래서 Receiver에서 ZeroPayload로 Id만 받고 fetch하는거.

반영: [[ADR-004] 인메모리 우선 인프라 채택](/docs/ADR/%5BADR-004%5D%20인메모리%20우선%20인프라%20채택.md) 근거 보강 — payload 최소화 + 처리 시점 fetch가 전달 의미론 의존을 낮춘다.

**Q5 보충 — diff는 의도를 잃지 않나? (score 0이 죽음인지 리셋인지)**
> old를 같이 보내는 이유가 그래서 그런거고, 애초에 순서적 합리를 좀 버리면 new 시점만으로 컨트롤이 가능은!(그러나 매우매우 구림) 함.

반영: [[RFC-009] Emitter](/docs/RFC/%5BRFC-009%5D%20Emitter.md) 규칙 보강 — old/new 쌍이 전이의 의미를 보존한다.

**Q9 보충 — 예외가 Handler로 역전파되는 것은 "실패는 그 단에서 끝난다"와 어긋나지 않나?**
> 실패가 다른 Event를 만들지 않으면 충분, 그냥 적당한 Scope 안에 담기면 됨.

반영: [[ADR-005] 데이터 정합성 수준 채택](/docs/ADR/%5BADR-005%5D%20데이터%20정합성%20수준%20채택.md) 결정 명확화 — 격리 기준은 예외 전파 차단이 아니라 추가 Event 미발행.

