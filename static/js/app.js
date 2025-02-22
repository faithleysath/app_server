const { createApp } = Vue;
const { ElMessage } = ElementPlus;

const app = createApp({
    data() {
        return {
            // 登录状态
            isLoggedIn: false,
            token: localStorage.getItem('token'),
            loginForm: {
                username: '',
                password: ''
            },

            // 标签页状态
            activeTab: 'auth',

            // 授权规则状态
            authRules: [],
            showAuthDialog: false,
            dialogTitle: '添加授权规则',
            authForm: {
                id: null,
                app: '',
                version_rule: '',
                ip_rule: '',
                detail_info: ''
            },

            // 事件记录状态
            events: [],
            eventFilter: {
                app: '',
                event_type: ''
            },

            // 统计报表状态
            statsFilter: {
                dateRange: []
            },
            stats: []
        }
    },

    methods: {
        // 登录处理
        async handleLogin() {
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.loginForm)
                });

                if (response.ok) {
                    const data = await response.json();
                    this.token = data.data.token;
                    localStorage.setItem('token', this.token);
                    this.isLoggedIn = true;
                    this.loadAuthRules();
                } else {
                    const error = await response.json();
                    ElMessage.error(error.detail || '登录失败');
                }
            } catch (error) {
                ElMessage.error('登录请求失败');
            }
        },

        // 退出登录
        handleLogout() {
            this.isLoggedIn = false;
            this.token = null;
            localStorage.removeItem('token');
        },

        // 获取请求headers
        getHeaders() {
            const headers = {
                'Content-Type': 'application/json'
            };
            if (this.token) {
                headers['Authorization'] = `Bearer ${this.token}`;
            }
            return headers;
        },

        // 加载授权规则
        async loadAuthRules() {
            try {
                const response = await fetch('/api/auth/list', {
                    headers: this.getHeaders()
                });
                if (response.ok) {
                    const data = await response.json();
                    this.authRules = data.data;
                }
            } catch (error) {
                ElMessage.error('加载授权规则失败');
            }
        },

        // 显示添加授权规则对话框
        showAddAuthDialog() {
            this.authForm = {
                id: null,
                app: '',
                version_rule: '',
                ip_rule: '',
                detail_info: ''
            };
            this.dialogTitle = '添加授权规则';
            this.showAuthDialog = true;
        },

        // 编辑授权规则
        editAuth(row) {
            this.authForm = { ...row };
            this.dialogTitle = '编辑授权规则';
            this.showAuthDialog = true;
        },

        // 保存授权规则
        async saveAuth() {
            try {
                const url = this.authForm.id ? '/api/auth/update' : '/api/auth/create';
                const response = await fetch(url, {
                    method: 'POST',
                    headers: this.getHeaders(),
                    body: JSON.stringify(this.authForm)
                });

                if (response.ok) {
                    ElMessage.success('保存成功');
                    this.showAuthDialog = false;
                    this.loadAuthRules();
                }
            } catch (error) {
                ElMessage.error('保存失败');
            }
        },

        // 删除授权规则
        async deleteAuth(row) {
            try {
                const response = await fetch(`/api/auth/delete/${row.id}`, {
                    method: 'DELETE',
                    headers: this.getHeaders()
                });

                if (response.ok) {
                    ElMessage.success('删除成功');
                    this.loadAuthRules();
                }
            } catch (error) {
                ElMessage.error('删除失败');
            }
        },

        // 加载事件记录
        async loadEvents() {
            try {
                const params = new URLSearchParams();
                if (this.eventFilter.app) {
                    params.append('app', this.eventFilter.app);
                }
                if (this.eventFilter.event_type) {
                    params.append('event_type', this.eventFilter.event_type);
                }

                const response = await fetch(`/api/events?${params.toString()}`, {
                    headers: this.getHeaders()
                });
                if (response.ok) {
                    const data = await response.json();
                    this.events = data.data;
                }
            } catch (error) {
                ElMessage.error('加载事件记录失败');
            }
        },

        // 生成统计报表
        async generateStats() {
            try {
                const params = new URLSearchParams();
                if (this.statsFilter.dateRange && this.statsFilter.dateRange.length === 2) {
                    params.append('start_date', this.statsFilter.dateRange[0]);
                    params.append('end_date', this.statsFilter.dateRange[1]);
                }

                const response = await fetch(`/api/stats?${params.toString()}`, {
                    headers: this.getHeaders()
                });
                if (response.ok) {
                    const data = await response.json();
                    this.stats = data.data;
                }
            } catch (error) {
                ElMessage.error('生成报表失败');
            }
        }
    },

    mounted() {
        if (this.token) {
            this.isLoggedIn = true;
            this.loadAuthRules();
        }
    }
});

app.use(ElementPlus);
app.mount('#app');
