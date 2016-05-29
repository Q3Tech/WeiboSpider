<template>
    <div>
        <!-- main view -->
        <p>舆情分析平台</p>
        <a href="#!/wordfollow/">关键词跟踪</a>
        <a href="#!/wordfollow-control/">关键词跟踪控制</a>
        <router-view
            class="view"
            keep-alive
            transition
            transition-mode="out-in">
        </router-view>
    </div>
</template>
