// 코스 메타데이터 — 원본: https://cvg.ethz.ch/lectures/Robot-Learning/ (Oier Mees, ETH Zurich, Spring 2026)
const ORIGIN = "https://cvg.ethz.ch/lectures/Robot-Learning/";

const COURSE = {
  weeks: [
    {
      week: 1, date: "2월 16일", key: "lec01", video: "X0k14u6pSxw",
      title_ko: "로봇 러닝 입문", title_en: "Introduction to Robot Learning",
      slides: ORIGIN + "lectures/lecture1_intro.pdf",
      papers: [],
      guest: null,
    },
    {
      week: 2, date: "2월 23일", key: "lec02", video: "5-Bb84eTTqQ",
      title_ko: "로봇 제어와 MDP", title_en: "Robot Control & MDPs",
      slides: ORIGIN + "lectures/lecture2_control_mdp.pdf",
      papers: [
        { t: "Simple random search provides a competitive approach to RL", a: "Mania et al., 2018", u: "https://arxiv.org/abs/1803.07055" },
        { t: "Deep RL Doesn't Work Yet", a: "Irpan, 2018", u: "https://www.alexirpan.com/2018/02/14/rl-hard.html" },
        { t: "Curiosity-driven Exploration by Self-supervised Prediction", a: "Pathak et al., 2017", u: "https://arxiv.org/pdf/1705.05363" },
      ],
      guest: { name: "Abhishek Gupta", affil: "워싱턴대 교수", url: "https://homes.cs.washington.edu/~abhgupta/", key: "guest02", video: "aG8NPTPhwkE" },
    },
    {
      week: 3, date: "3월 2일", key: "lec03", video: "Ef4R5s1LqoQ",
      title_ko: "모방 학습", title_en: "Imitation Learning",
      slides: ORIGIN + "lectures/lecture3_imitation.pdf",
      papers: [
        { t: "Causal Confusion in Imitation Learning", a: "de Haan et al., 2019", u: "https://arxiv.org/abs/1905.11979" },
        { t: "The Surprising Effectiveness of Representation Learning for Visual Imitation", a: "Pari et al., 2021", u: "https://arxiv.org/abs/2112.01511" },
        { t: "Transporter Networks: Rearranging the Visual World for Robotic Manipulation", a: "Zeng et al., 2020", u: "https://arxiv.org/pdf/2010.14406" },
      ],
      guest: { name: "Danfei Xu", affil: "조지아텍 교수", url: "https://faculty.cc.gatech.edu/~danfei/", key: "guest03", video: "qvTP6T5oq1w" },
    },
    {
      week: 4, date: "3월 9일", key: "lec04", video: "90raNpc11tQ",
      title_ko: "강화 학습 I", title_en: "Reinforcement Learning I",
      slides: ORIGIN + "lectures/lecture4_rl_I.pdf",
      papers: [
        { t: "Evolution Strategies as a Scalable Alternative to RL", a: "Salimans et al., 2017", u: "https://arxiv.org/abs/1703.03864" },
        { t: "Learning Synergies between Pushing and Grasping", a: "Zeng et al., 2018", u: "https://arxiv.org/abs/1803.09956" },
        { t: "Precise and Dexterous Robotic Manipulation via Human-in-the-Loop RL", a: "Luo et al., 2024", u: "https://arxiv.org/pdf/2410.21845" },
      ],
      guest: { name: "Aviral Kumar", affil: "CMU 교수 & Google DeepMind", url: "https://aviralkumar2907.github.io/", key: "guest04", video: "fHHLmTu9sFk" },
    },
    {
      week: 5, date: "3월 16일", key: "lec05", video: "AdTGz8YnnlE",
      title_ko: "강화 학습 II", title_en: "Reinforcement Learning II",
      slides: ORIGIN + "lectures/lecture5_rl_II.pdf",
      papers: [
        { t: "End-to-End Training of Deep Visuomotor Policies", a: "Levine et al., 2015", u: "https://arxiv.org/abs/1504.00702" },
        { t: "Eureka: Human-Level Reward Design via Coding LLMs", a: "Ma et al., 2023", u: "https://arxiv.org/abs/2310.12931" },
        { t: "Latent Plans for Task Agnostic Offline RL", a: "Rosete-Beas et al., 2022", u: "https://arxiv.org/pdf/2209.08959" },
      ],
      guest: { name: "Andrew Wagenmaker", affil: "UC 버클리 포스닥", url: "https://wagenmaker.github.io/", key: "guest05", video: "CPmTpXA5azw" },
    },
    {
      week: 6, date: "3월 23일", key: "lec06", video: "qd6Ldsuu46I",
      title_ko: "생성 모델", title_en: "Generative Models",
      slides: ORIGIN + "lectures/lecture6_generative.pdf",
      papers: [
        { t: "Planning with Diffusion for Flexible Behavior Synthesis", a: "Janner & Du et al., 2022", u: "https://arxiv.org/abs/2205.09991" },
        { t: "Implicit Behavioral Cloning", a: "Florence et al., 2021", u: "https://arxiv.org/pdf/2109.00137" },
        { t: "Steering Your Diffusion Policy with Latent Space RL", a: "Wagenmaker et al., 2025", u: "https://arxiv.org/abs/2506.15799" },
      ],
      guest: { name: "Cheng Chi", affil: "Sunday Robotics 공동창업자 · Diffusion Policy & UMI 리드", url: "https://cheng-chi.github.io/", key: "guest06", video: "tvFvIEOBKfM" },
    },
    {
      week: 7, date: "3월 30일", key: "lec07", video: "imSTfMJjp7M",
      title_ko: "시퀀스 모델링과 트랜스포머", title_en: "Sequence Modeling and Transformers",
      slides: ORIGIN + "lectures/lecture7_sequence_modeling.pdf",
      papers: [
        { t: "Decision Transformer: RL via Sequence Modeling", a: "Chen et al., 2021", u: "https://arxiv.org/abs/2106.01345" },
        { t: "Learning Fine-Grained Bimanual Manipulation (ALOHA)", a: "Zhao et al., 2023", u: "https://arxiv.org/abs/2304.13705" },
        { t: "Humanoid Locomotion as Next Token Prediction", a: "Radosavovic et al., 2024", u: "https://arxiv.org/pdf/2402.19469" },
      ],
      guest: { name: "Ted Xiao", affil: "Prometheus 공동창업자, ex-Google", url: "https://tedxiao.me/", key: "guest07", video: "VS7Ulaugevg" },
    },
    {
      week: 8, date: "4월 13일", key: "lec08", video: "cTTmUZlOF2s",
      title_ko: "월드 모델", title_en: "World Models",
      slides: ORIGIN + "lectures/lecture8_world_models.pdf",
      papers: [
        { t: "Learning Universal Policies via Text-Guided Video Generation", a: "Du et al., 2023", u: "https://arxiv.org/abs/2302.00111" },
        { t: "Training Agents Inside of Scalable World Models", a: "Hafner et al., 2025", u: "https://arxiv.org/abs/2509.24527" },
        { t: "World Action Models are Zero-shot Policies (DreamZero)", a: "Ye et al., 2026", u: "https://dreamzero0.github.io/DreamZero.pdf" },
      ],
      guest: { name: "Scott Reed", affil: "NVIDIA GEAR Lab 수석연구원", url: "https://reedscot.github.io/", key: "guest08", video: "fqkp_wkov6M" },
    },
    {
      week: 9, date: "4월 27일", key: "lec09", video: "dtofzDY9zuo",
      title_ko: "범용 로봇 정책", title_en: "Generalist Robot Policies",
      slides: ORIGIN + "lectures/lecture9_generalist_policies.pdf",
      papers: [
        { t: "Language Conditioned Imitation Learning over Unstructured Data", a: "Lynch et al., 2021", u: "https://arxiv.org/pdf/2005.07648" },
        { t: "A Generalist Agent (Gato)", a: "Reed et al., 2022", u: "https://arxiv.org/abs/2205.06175" },
        { t: "π*0.6: a VLA That Learns From Experience", a: "Physical Intelligence, 2025", u: "https://arxiv.org/abs/2511.14759" },
      ],
      guest: { name: "Quan Vuong", affil: "Physical Intelligence 공동창업자", url: "https://scholar.google.com/citations?user=NSWI3OwAAAAJ&hl=en", key: "guest09", video: "pzolgvyWEFY" },
    },
    {
      week: 10, date: "5월 4일", key: "lec10", video: "CxhrjQuGEuE",
      title_ko: "체화된 추론과 테스트타임 스케일링", title_en: "Embodied Reasoning and Test-time Scaling",
      slides: ORIGIN + "lectures/lecture10_reasoning.pdf",
      papers: [
        { t: "In-Context Imitation Learning via Next-Token Prediction", a: "Fu et al., 2024", u: "https://arxiv.org/pdf/2408.15980" },
        { t: "VOYAGER: An Open-Ended Embodied Agent with LLMs", a: "Wang et al., 2023", u: "https://arxiv.org/abs/2305.16291" },
        { t: "Training Strategies for Efficient Embodied Reasoning", a: "Chen et al., 2025", u: "https://arxiv.org/pdf/2505.08243" },
      ],
      guest: { name: "Archit Sharma", affil: "Google DeepMind 연구원 · Gemini Deep Think 공동개발", url: "https://architsharma97.github.io", key: "guest10", video: "oBEkY6NeE_o" },
    },
    {
      week: 11, date: "5월 11일", key: "lec11", video: "eL4lcy1KNzE",
      title_ko: "최전선과 미해결 문제들", title_en: "Frontiers & Open Problems",
      slides: ORIGIN + "lectures/lecture11_frontiers.pdf",
      papers: [
        { t: "A Path Towards Autonomous Machine Intelligence", a: "LeCun, 2022", u: "https://openreview.net/pdf?id=BZ5a1r-kVsf" },
        { t: "The Bitter Lesson", a: "Sutton, 2019", u: "http://www.incompleteideas.net/IncIdeas/BitterLesson.html" },
        { t: "Intelligence without Representation", a: "Brooks, 1991", u: "https://people.csail.mit.edu/brooks/papers/representation.pdf" },
      ],
      guest: { name: "Lucas Beyer", affil: "Meta Superintelligence Labs", url: "https://lucasb.eyer.be/", key: "guest11", video: "0XB7fNS_ONg" },
    },
  ],
  tutorials: [
    { week: "1주차 · 2월 19일", topic: "PyTorch & NumPy 튜토리얼",
      url: "https://github.com/wngjs3/robot-learning-course-kr/tree/main/homework/hw1_pytorch_tutorial",
      orig: "https://github.com/mees-robot-learning-course/ethz-course-2026/tree/main/hw1_pytorch_tutorial" },
    { week: "2주차 · 2월 26일", topic: "로봇 제어와 MDP",
      url: "https://github.com/wngjs3/robot-learning-course-kr/tree/main/homework/hw2_robot_control_mdps",
      orig: "https://github.com/mees-robot-learning-course/ethz-course-2026/tree/main/hw2_robot_control_mdps" },
    { week: "3주차 · 3월 2일", topic: "모방 학습",
      url: "https://github.com/wngjs3/robot-learning-course-kr/tree/main/homework/hw3_imitation_learning",
      orig: "https://github.com/mees-robot-learning-course/ethz-course-2026/tree/main/hw3_imitation_learning" },
    { week: "5주차 · 3월 29일", topic: "강화 학습",
      url: "https://github.com/wngjs3/robot-learning-course-kr/tree/main/homework/hw4_reinforcement_learning",
      orig: "https://github.com/mees-robot-learning-course/ethz-course-2026/tree/main/hw4_reinforcement_learning" },
  ],
};

// 영상 키 → 주차/메타 빠른 조회
const VIDEO_INDEX = {};
COURSE.weeks.forEach((w) => {
  if (w.key) VIDEO_INDEX[w.key] = { type: "lecture", week: w };
  if (w.guest && w.guest.key) VIDEO_INDEX[w.guest.key] = { type: "guest", week: w };
});

// 재생 페이지의 이전/다음 내비게이션 순서
const PLAY_ORDER = [];
COURSE.weeks.forEach((w) => {
  if (w.key) PLAY_ORDER.push(w.key);
  if (w.guest && w.guest.key) PLAY_ORDER.push(w.guest.key);
});
