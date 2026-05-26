
library(tidyverse)

script_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
script_dir <- if (length(script_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", script_arg[1]), mustWork = TRUE))
} else {
  getwd()
}
repo_root <- normalizePath(file.path(script_dir, ".."), mustWork = TRUE)
setwd(repo_root)

save_path <- file.path(repo_root, "figures")
dir.create(save_path, recursive = TRUE, showWarnings = FALSE)

df<- read.csv("results/benchmark_1M.csv")

 
df <- df %>%
  mutate(System = recode(System,
                         "Karina" = "Titan RTX  (22 GB)",
                         "v100" = "Titan V       (12 GB)"))


df_plot<- df %>% group_by(System,Resource) %>% summarise(ME=mean(SOLVER_TIME),SD=sd(SOLVER_TIME))

# Filter for Karina only
karina_df <- df_plot %>% filter(System == "Titan RTX  (22 GB)")

# Find the x positions for the first and last bars
first_x <-  karina_df$Resource[1] 
last_x  <-  karina_df$Resource[nrow(karina_df)] 

# Find the y positions (mean values) for the first and last bars
first_y <- karina_df$ME[1]
last_y  <- karina_df$ME[nrow(karina_df)]


ggplot(karina_df, aes(x = factor(Resource), y = ME)) +
  geom_col(fill = "#66c2a5",width = 0.7) + theme_classic() +
  geom_errorbar(aes(ymin = ME - SD, ymax = ME + SD), width = 0.2) +
  geom_text(aes(label = round(ME)), vjust = -0.5, size = 9) +  
  theme(legend.position= "none",
        legend.key.size =  unit(4, "lines"),
        legend.spacing.x = unit(0.1,"mm"),
        legend.text = element_text(size=18),
        strip.text = element_text(size = 20),  # facet text size
        #strip.background = element_blank() , 
        #strip.background =element_rect(fill = facet_colors[levels(four_rois_data$roi)], color = NA), # Apply colors
        legend.margin = margin(t = -40),  # spacing between x axis and legend
        axis.ticks.length.x = unit(3,'mm'),
        axis.ticks.length.y = unit(3,'mm'), 
        axis.text = element_text(size=28),
        #axis.text.x =  element_blank(),
        axis.title.x = element_text(size=28),
        axis.title.y = element_text(size=28),
        plot.title = element_text(size=28,hjust = 0.5), 
        legend.title = element_blank()) +
  scale_y_continuous(breaks = c(0,250,500),limits = c(0,550),
                     expand = c(0,0))  + 
  scale_x_discrete(expand = expansion(add = 0.9)) +
  labs(x = "Number of GPUs", y = "Solver Time (s) ")  +
  annotate("text", x = first_x+0.57, y = first_y + 19, 
           label = "(3.4x)", color = "red", size = 9) +
  annotate("text", x = last_x+0.58 , y = last_y + 20, 
           label = "(9.8x)", color = "red", size = 9) #+
  #annotate("text", x = 3.3 , y = 455, 
  #         label = "Compared to CPU run", color = "red", size =10)
 

ggsave(file.path(save_path,'Turing.eps'),width = 8, height=9,dpi = 300) 

  


# Filter for GPU 1 and 2 only
compare_df <- df_plot %>% filter(Resource %in% c(1, 2))

ggplot(compare_df, aes(x = factor(Resource), y = ME, fill =  System)) + theme_classic() +
  geom_col(position = position_dodge(width = 0.8), width = 0.75) +
  geom_errorbar(aes(ymin = ME - SD, ymax = ME + SD), 
                position = position_dodge(width = 0.8), width = 0.2) + 
  geom_text(aes(label = round(ME)), 
            position = position_dodge(width = 0.8), 
            vjust = -0.5, size = 9) +
  labs(x = "Number of GPUs", y = "Solver Time (s)", fill = "HPC environment",
       title = "") +
  theme(legend.position= c(0.75,0.9),
        legend.key.size =  unit(1.5, "lines"),
        legend.spacing.x = unit(0.5,"mm"),
        legend.text = element_text(size=24),
        strip.text = element_text(size = 20),  # facet text size
        #strip.background = element_blank() , 
        #strip.background =element_rect(fill = facet_colors[levels(four_rois_data$roi)], color = NA), # Apply colors
        legend.margin = margin(t = -40),  # spacing between x axis and legend
        axis.ticks.length.x = unit(3,'mm'),
        axis.ticks.length.y = unit(3,'mm'), 
        axis.text = element_text(size=28),
        #axis.text.x =  element_blank(),
        axis.title.x = element_text(size=28),
        axis.title.y = element_text(size=28),
        plot.title = element_text(size=28,hjust = 0.5), 
        legend.title = element_text(size=26,hjust = 0.5,vjust=1)) +
  scale_y_continuous(breaks =  c(0,250,500),limits = c(0,570),
                     expand = c(0,0))+
  scale_fill_manual(values = c("#66c2a5" , "#fc8d62" )) +
  annotate("text", x = 2.53  , y =  270, 
           label = "(6.7x)", color = "red", size = 9)  +
  scale_x_discrete(expand = expansion(add = 0.7)) 
  #scale_fill_manual(values = c("#1f77b4", "#ff7f0e")) 
 
 

ggsave(file.path(save_path,'HPCcompare.eps'),width = 8, height=9,dpi = 300) 

# theme(plot.title = element_text(hjust = 0.5))




###############################################################################
# model building compuation time for 1M cells

library(tidyverse)

df<- read.csv("results/benchmark_model_building.csv")

 
df <- df %>%
  mutate(System = recode(System,
                         "Karina" = "Titan RTX  (22 GB)",
                         "v100" = "Titan V       (12 GB)"))


df_plot<- df %>% group_by(System,Resource) %>% summarise(ME=mean(ModelBuilding),SD=sd(ModelBuilding))

# Filter for Karina only
karina_df <- df_plot %>% filter(System == "Titan RTX  (22 GB)")

# Find the x positions for the first and last bars
first_x <-  karina_df$Resource[1] 
last_x  <-  karina_df$Resource[nrow(karina_df)] 

# Find the y positions (mean values) for the first and last bars
first_y <- karina_df$ME[1]
last_y  <- karina_df$ME[nrow(karina_df)]


ggplot(karina_df, aes(x = factor(Resource), y = ME)) +
  geom_col(fill = "#66c2a5",width = 0.7) + theme_classic() +
  geom_errorbar(aes(ymin = ME - SD, ymax = ME + SD), width = 0.2) +
  geom_text(aes(label = round(ME)), vjust = -0.5, size = 9) +  
  theme(legend.position= "none",
        legend.key.size =  unit(4, "lines"),
        legend.spacing.x = unit(0.1,"mm"),
        legend.text = element_text(size=18),
        strip.text = element_text(size = 20),  # facet text size
        #strip.background = element_blank() , 
        #strip.background =element_rect(fill = facet_colors[levels(four_rois_data$roi)], color = NA), # Apply colors
        legend.margin = margin(t = -40),  # spacing between x axis and legend
        axis.ticks.length.x = unit(3,'mm'),
        axis.ticks.length.y = unit(3,'mm'), 
        axis.text = element_text(size=28),
        #axis.text.x =  element_blank(),
        axis.title.x = element_text(size=28),
        axis.title.y = element_text(size=28),
        plot.title = element_text(size=28,hjust = 0.5), 
        legend.title = element_blank()) +
  scale_y_continuous(breaks = c(0,200,400),limits = c(0,450),
                     expand = c(0,0))  + 
  scale_x_discrete(expand = expansion(add = 0.9)) +
  labs(x = "Number of GPUs", y = "Model Building Time (s)")  +
  annotate("text", x = first_x+0.57, y = first_y + 15, 
           label = "(2.9x)", color = "red", size = 9) +
  annotate("text", x = last_x+0.58 , y = last_y + 15, 
           label = "(8.4x)", color = "red", size = 9) +
  annotate("text", x = 3.3 , y = 350, 
           label = "Compared to CPU run", color = "red", size =10) +
  annotate("text", x = 3.3 , y = 425, 
           label = "Titan RTX", color = "blue", size =10)   

ggsave(file.path(save_path,'Turing_ModelBuilding.eps'),width = 8, height=9,dpi = 300) 

 

# Filter for GPU 1 and 2 only
compare_df <- df_plot %>% filter(Resource %in% c(1, 2))

ggplot(compare_df, aes(x = factor(Resource), y = ME, fill =  System)) + theme_classic() +
  geom_col(position = position_dodge(width = 0.8), width = 0.75) +
  geom_errorbar(aes(ymin = ME - SD, ymax = ME + SD), 
                position = position_dodge(width = 0.8), width = 0.2) + 
  geom_text(aes(label = round(ME)), 
            position = position_dodge(width = 0.8), 
            vjust = -0.5, size = 9) +
  labs(x = "Number of GPUs", y = "Model Building Time (s)", fill = "HPC environment",
       title = "") +
  theme(legend.position= c(0.75,0.9),
        legend.key.size =  unit(1.5, "lines"),
        legend.spacing.x = unit(0.5,"mm"),
        legend.text = element_text(size=24),
        strip.text = element_text(size = 20),  # facet text size
        #strip.background = element_blank() , 
        #strip.background =element_rect(fill = facet_colors[levels(four_rois_data$roi)], color = NA), # Apply colors
        legend.margin = margin(t = -40),  # spacing between x axis and legend
        axis.ticks.length.x = unit(3,'mm'),
        axis.ticks.length.y = unit(3,'mm'), 
        axis.text = element_text(size=28),
        #axis.text.x =  element_blank(),
        axis.title.x = element_text(size=28),
        axis.title.y = element_text(size=28),
        plot.title = element_text(size=28,hjust = 0.5), 
        legend.title = element_text(size=26,hjust = 0.5,vjust=1)) +
  scale_y_continuous(breaks =  c(0,200,400),limits = c(0,450),
                     expand = c(0,0))+
  scale_fill_manual(values = c("#66c2a5" , "#fc8d62" )) +
  annotate("text", x = 2.53  , y =  187, 
           label = "(6.8x)", color = "red", size = 9)  +
  scale_x_discrete(expand = expansion(add = 0.7)) 
#scale_fill_manual(values = c("#1f77b4", "#ff7f0e"))  


ggsave(file.path(save_path,'HPCcompare_ModelBuilding.eps'),width = 8, height=9,dpi = 300) 

