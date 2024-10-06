<template>
    <nav class="navbar">
        <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
        <ul class="options" v-if="show||widescreen">
            <div class="divider"></div>
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <div class="divider"></div>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <div class="divider"></div>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <div class="divider"></div>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>

        <button class="hamburger" @click="hide()">&#9776;</button>
    </nav>
    
    
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'NavBar',
    data() {
        return {
            show: false,
            widescreen: window.innerWidth > 768,
        }
    },
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    methods: {
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
        },
        hide(){
            this.show = !this.show
        },
        handleResize() {
            this.widescreen = window.innerWidth > 768;
            if (this.widescreen) {
                this.show = false; // 在寬螢幕下隱藏漢堡選單
            }
        },
    },
    mounted() {
        window.addEventListener('resize', this.handleResize);
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    height: 4.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
}

.divider{
    display: none;
}
.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title > a{
    font-size: 1.4em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

.hamburger {
    display: none;
    font-size: 1.5rem;
    cursor: pointer;
    position: absolute;
    top: 1rem;
    right: 1rem; /* 將按鈕移至右上角 */
}

@media (max-width: 768px) {

    .divider {
        display: block;
        border: .2em solid #f3f3f3;
        width: 100%; /* 控制分隔線的寬度 */
        border-top: 1px solid rgba(175, 175, 175, 0.5); /* 半透明灰色線 */
    }
    .navbar ul {
        position: fixed;
        top: 72px;
        left: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        background-color: #f3f3f3;
    }

    .navbar li {
        font-size: 1.1em;
    }

    .hamburger {
        display: block;
    }
}
</style>